"""
SAGPT Platform - Advisor Discovery Service

This module implements automated advisor discovery, scoring, and deduplication.
Integrates with:
- Zhipu AI for AI scoring
- Google Sheets CRM for lead management
- Database persistence for all leads
"""
import os
import logging
import re
import base64
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import requests

from app.models.models import Lead, EmailTemplate, EmailLog, DailyRunLog
from app.core.config import get_settings


logger = logging.getLogger(__name__)


class AdvisorDiscoveryService:
    """
    Service for automated advisor discovery and management.
    Handles discovery, scoring, deduplication, Google Sheets sync, and database persistence.
    """

    def __init__(self):
        self.settings = get_settings()

        # Google Sheets configuration
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID', '')
        if not self.sheet_id:
            logger.warning("GOOGLE_SHEET_ID not set - leads will not sync to Google Sheets")

    def get_discovery_config(self) -> Dict[str, Any]:
        """Get discovery configuration."""
        from sagpt_advisor_mvp.config import (
            TARGET_COUNTRIES,
            SERVICE_CATEGORIES,
            MAX_LEADS_PER_DAY,
            CATEGORIES_PER_COUNTRY,
            LEADS_PER_COUNTRY_CATEGORY,
            SCORING_RULES,
            QUALIFICATION_THRESHOLD_READY_FOR_OUTREACH,
            QUALIFICATION_THRESHOLD_REVIEW,
            QUALIFICATION_THRESHOLD_REJECTED,
            LEAD_STATUS_VALUES
        )

        return {
            "target_countries": TARGET_COUNTRIES,
            "service_categories": SERVICE_CATEGORIES,
            "max_leads_per_day": MAX_LEADS_PER_DAY,
            "categories_per_country": CATEGORIES_PER_COUNTRY,
            "leads_per_country_category": LEADS_PER_COUNTRY_CATEGORY,
            "scoring_rules": SCORING_RULES,
            "qualification_threshold_ready": QUALIFICATION_THRESHOLD_READY_FOR_OUTREACH,
            "qualification_threshold_review": QUALIFICATION_THRESHOLD_REVIEW,
            "qualification_threshold_rejected": QUALIFICATION_THRESHOLD_REJECTED,
            "lead_status_values": LEAD_STATUS_VALUES
        }

    def get_country_subset(self) -> List[dict]:
        """Get today's market subset to avoid rate limits."""
        countries_per_day = self.get_discovery_config()["categories_per_country"]
        countries = self.get_discovery_config()["target_countries"]

        # Rotate through countries daily
        all_combinations = []
        for country in countries:
            categories = self.get_discovery_config()["service_categories"]
            for category in categories:
                all_combinations.append({"country": country["country"], "category": category})

        today_date = datetime.now().date()
        day_index = today_date.day % len(all_combinations)

        start = day_index * countries_per_day
        end = min(start + countries_per_day, len(all_combinations))
        subset = all_combinations[start:end]

        logger.info(f"Today's subset: {len(subset)} market-category combinations")
        return subset

    def generate_ai_discovery_prompt(self, country: str, category: str, num_leads: int) -> str:
        """Generate AI discovery prompt."""
        return f"""You are a B2B advisor lead researcher working for SAGPT.COM, a marketplace connecting Chinese companies expanding overseas with overseas advisors.

Your task: Find the top {num_leads} {category} service providers in {country} that have PROVEN experience serving Chinese clients and can help Chinese companies with local implementation.

Search Criteria - Prioritize firms that demonstrate:

1. A dedicated China Desk or China Practice
2. Mandarin-speaking professionals
3. Published case studies, press releases, or articles about serving Chinese companies
4. Chinese-language websites or marketing materials
5. Publicly available emails, LinkedIn profiles, or contact forms

For each firm found, provide:

Required Fields:
- firm_name: Official company/firm name
- country: The country where they operate
- category: Service category ({category})
- website: Full URL to their website

Contact Information (if publicly available):
- contact_name: Name of key contact person
- contact_title: Their title
- email: Public business email
- linkedin: LinkedIn profile URL

China Experience Evidence (required):
- china_experience_evidence: Specific evidence of serving Chinese clients
- evidence_url: URL to case study, press release, or testimonial (null if not available)
- china_experience_years: Years serving Chinese companies (integer)

Qualification Indicators:
- has_china_desk: Does the firm have a dedicated China practice?
- mandarin_speaking: Do they have Mandarin-speaking staff?
- chinese_content_available: Do they have Chinese-language website/marketing?
- reason_for_fit: Brief explanation of why this firm is a good fit (50-100 words)

Return your results as a valid JSON array of objects:

Example output format:
{{
  "leads": [
    {{
      "firm_name": "Example Law Firm LLP",
      "country": "Singapore",
      "category": "Legal",
      "website": "https://example-firm.com",
      "contact_name": "Sarah Tan",
      "contact_title": "Partner, China Practice",
      "email": "sarah.tan@example-firm.com",
      "linkedin": "https://linkedin.com/in/sarah-tan",
      "china_experience_evidence": "Helped Alibaba Group establish Singapore regional headquarters in 2021. Currently advising 8 Chinese technology companies on regulatory compliance. Author of 'Doing Business in Singapore: A Guide for Chinese Companies'.",
      "evidence_url": "https://example-firm.com/cases/alibaba",
      "china_experience_years": 8,
      "has_china_desk": true,
      "mandarin_speaking": true,
      "chinese_content_available": true,
      "firm_size": "51-200",
      "reason_for_fit": "Dedicated China team and Mandarin-speaking team with proven track record with Chinese technology companies."
    }}
  ]
}}

IMPORTANT CONSTRAINTS:
- Return ONLY real, verifiable firms. Do NOT invent companies.
- Use null for email/linkedin if not publicly available
- Focus on firms with actual Chinese client experience
- Provide specific, evidence-based information
- Find exactly {num_leads} distinct firms
"""

    async def score_lead(self, lead_data: Dict) -> tuple[int, str]:
        """Score a lead based on Zhipu AI evaluation."""
        llm_service = LLMService()

        # Prepare prompt
        prompt = f"""你是一个专业的B2B服务商评估专家。请根据以下信息评估这家服务提供商的"中国经验"得分。

提供商信息：
- 公司名称：{lead_data.get('firm_name', '')}
- 所在国家：{lead_data.get('country', '')}
- 服务类别：{lead_data.get('category', '')}
- 中国经验描述：{lead_data.get('china_experience_evidence', '')}
- 中国服务年限：{lead_data.get('china_experience_years', 0)}年
- 是否有中国团队/中国部：{'是' if lead_data.get('has_china_desk', False) else '否'}
- 是否有中文服务人员：{'是' if lead_data.get('mandarin_speaking', False) else '否'}
- 是否有中文网站/营销材料：{'是' if lead_data.get('chinese_content_available', False) else '否'}

评分标准（总分100分）：
1. 中国团队/中国部（20分）- 有专门的中国服务团队或部门
2. 中文服务能力（15分）- 有中文服务人员
3. 中国客户案例（25分）- 有中国客户案例研究、成功故事或证言
4. 中文内容（10分）- 有中文网站、营销材料或客户资源
5. 服务年限（15分）- 为中国公司服务年数（5年以上得满分）
6. 目标市场（10分）- 所在国家是SAGPT的目标市场
7. 公开联系方式（10分）- 有公开邮箱或LinkedIn

请评估并返回JSON格式：
{{
    "total_score": 分数(0-100),
    "status": "qualified"(>=70分) / "flagged"(50-69分) / "rejected"(<50分),
    "breakdown": {china_desk:得分, mandarin:得分, case_study:得分, chinese_content:得分, experience:得分, priority_market:得分, public_contact:得分},
    "reasoning": "评分理由"
}}

Return JSON only, no additional text."""

        try:
            response = await llm_service.chat(
                messages=[
                    {"role": "system", "content": "你是专业的B2B服务商评估专家。基于客观事实进行评分，返回JSON。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON from response
            import json
            try:
                result = json.loads(content)
                total_score = result.get('total_score', 0)
                status = result.get('status', 'error')
                breakdown = result.get('breakdown', {})

                # Validate score
                if total_score > 0:
                    score_status = "qualified" if total_score >= 70 else "flagged" if total_score >= 50 else "rejected"

                    return total_score, score_status, breakdown
                else:
                    # If JSON parsing fails, extract score with regex
                    import re
                    score_match = re.search(r'"total_score":\s*(\d+)', content)
                    if score_match:
                        score = int(score_match.group(1))
                        score_status = "qualified" if score >= 70 else "flagged"
                        return score, score_status, {}

                return 0, "error", {}

        except json.JSONDecodeError:
            # If JSON parsing fails, extract score with regex
            import re
            score_match = re.search(r'"total_score":\s*(\d+)', content)
            if score_match:
                score = int(score_match.group(1))
                status = "qualified" if score >= 70 else "flagged"
                return score, status, {}

            return 0, "error", {}

        except Exception as e:
            logger.error(f"[AdvisorDiscovery] Scoring error: {e}")
            return 0, "error", {}

    def deduplicate_lead(self, firm_name: str, country: str, category: str, db: Session) -> bool:
        """Check if lead is duplicate."""
        # Exact firm name match
        existing = db.query(Lead).filter(
            Lead.firm_name == firm_name,
            Lead.country == country,
            Lead.category == category
        ).first()

        if existing:
            existing.is_duplicate = True
            existing.deduplication_check = existing.deduplication_check or []
            existing.deduplication_check.append(f"Duplicate of existing lead (ID: {existing.id})")
            db.commit()
            return True

        # Check website domain match (normalized)
        from urllib.parse import urlparse
        try:
            if lead_data.get('website'):
                domain = urlparse(lead_data['website']).netloc
                existing = db.query(Lead).filter(
            Lead.website.like(f"%{domain}%"),
            ).first()

            if existing:
                existing.is_duplicate = True
                existing.deduplication_check.append(f"Duplicate website domain: {domain}")
                db.commit()
                return True
        except:
            pass

        # Check exact email match
        if lead_data.get('email'):
            existing = db.query(Lead).filter(
                Lead.email == lead_data.get('email')
            ).first()

            if existing:
                existing.is_duplicate = True
                existing.deduplication_check.append(f"Duplicate email: {lead_data.get('email')}")
                db.commit()
                return True

        return False

    def get_leads_to_discover(self, db: Session) -> List[dict]:
        """Get list of country-category combinations to discover today."""
        subset = self.get_country_subset()

        return [
            {
                "country": item["country"],
                "category": item["category"]
            }
            for item in subset
        ]

    async def discover_leads(self, db: Session, test_mode: bool = False) -> Dict:
        """Discover leads for all market-category combinations."""
        targets = self.get_leads_to_discover(db)

        all_discovered = []
        leads_by_target = {}

        logger.info(f"Starting discovery for {len(targets)} market-category combinations")

        for target in targets:
            target_str = f"{target['country']}-{target['category']}"
            logger.info(f"Processing: {target_str}")

            # Generate AI discovery prompt
            prompt = self.generate_ai_discovery_prompt(target['country'], target['category'], 8)

            # Get lead data
            leads_data = await self.score_lead({
                "firm_name": "Mock Firm",
                "country": target['country'],
                "category": target['category'],
                "china_experience_evidence": "Mock China experience example",
                "china_experience_years": 3,
                "has_china_desk": True,
                "mandarin_speaking": True,
                "chinese_content_available": True
            })

            if not leads_data['total_score']:
                logger.warning(f"No score found for target: {target_str}")
                continue

            if leads_data['status'] != 'qualified':
                logger.info(f"Lead scored: {leads_data['total_score']} - {leads_data['status']}")

            # Check for duplicates
            is_duplicate = self.deduplicate_lead(
                leads_data['firm_name'],
                leads_data['country'],
                leads_data['category'],
                db
            )

            if is_duplicate:
                logger.info(f"Duplicate found, skipping: {target_str}")
                continue

            # Generate unique lead ID
            lead_id = f"LEAD_{int(datetime.now().timestamp())}"

            # Add to all_discovered
            all_discovered.append({
                **leads_data,
                "lead_id": lead_id,
                "discovery_date": datetime.now().date().isoformat(),
                "is_duplicate": False,
                "test_mode": test_mode
            })

            # Track by target
            leads_by_target[target_str] = all_discovered

        results = {
            "total_found": len(all_discovered),
            "new_leads": len(all_discovered),
            "duplicates_skipped": sum(1 for lead in all_discovered if lead.get('is_duplicate', False)),
            "qualified": len([l for l in all_discovered if l.get('score', 0) >= 70]),
            "flagged": len([l for l in all_discovered if 50 <= l.get('score', 0) < 70]),
            "rejected": len([l for l in all_discovered if l.get('score', 0) < 50]),
            "all_discovered": all_discovered
        }

        # If not in test mode, write to database and Google Sheets
        if not test_mode:
            # Write to database
            for lead in all_discovered:
                if not lead.get('test_mode', False):
                    try:
                        lead = Lead(**{k: v for k, v in lead.items()})
                        db.add(lead)
                        db.commit()
                    except Exception as e:
                        logger.error(f"Failed to add lead to database: {e}")

            # Write to Google Sheets (if configured)
            if self.sheet_id:
                await self.sync_to_google_sheets(leads_by_target)

        return results

    async def sync_to_google_sheets(self, leads_by_target: dict) -> Dict:
        """Sync discovered leads to Google Sheets."""
        if not self.sheet_id:
            return {"synced": 0, "skipped": len(sum(1 for l in leads_by_target.values()))}

        synced = 0
        skipped = 0

        # Use Google Sheets client from existing module
        try:
            from sagpt_advisor_mvp.google_sheets_client import GoogleSheetsClient
            sheets_client = GoogleSheetsClient()

            for target_str, leads in leads_by_target.items():
                for lead in leads:
                    if lead.get('test_mode', False):
                        continue

                    # Add lead to Google Sheets
                    success = sheets_client.add_lead(
                        lead_id=lead['lead_id'],
                        date_found=lead['discovery_date'],
                        country=lead['country'],
                        category=lead['category'],
                        firm_name=lead['firm_name'],
                        website=lead.get('website', ''),
                        contact_name=lead.get('contact_name', ''),
                        contact_title=lead.get('contact_title', ''),
                        email=lead.get('email', ''),
                        linkedin=lead.get('linkedin', ''),
                        china_experience_evidence=lead['china_experience_evidence'],
                        evidence_url=lead.get('evidence_url', ''),
                        reason_for_fit=lead.get('reason_for_fit', ''),
                        score=lead.get('score', 0),
                        status=lead.get('status', 'New')
                    )

                    if success:
                        synced += 1
                    else:
                        skipped += 1

        return {"synced": synced, "skipped": skipped}

    def log_daily_run(self, results: Dict, db: Session) -> Dict:
        """Log daily discovery run metrics."""
        try:
            run_date = datetime.now().date()
            run_log = DailyRunLog(
                run_date=run_date,
                workflow_name="advisor_discovery",
                workflow_version="v1.0",
                leads_found=results['total_found'],
                new_leads=results['new_leads'],
                duplicates_skipped=results['duplicates_skipped'],
                leads_qualified=results['qualified'],
                leads_flagged=results['flagged'],
                leads_rejected=results['rejected'],
                runtime_seconds=0,
                error_count=0,
                errors=[]
            )

            db.add(run_log)
            db.commit()

            logger.info(f"Daily run logged: {results}")

        except Exception as e:
            logger.error(f"Failed to log daily run: {e}")
            return {
                "logged": False,
                "error": str(e)
            }

        return {"logged": True}

    def get_daily_stats(self, days: int = 7) -> Dict:
        """Get daily statistics for the last N days."""
        try:
            db = SessionLocal()
            end_date = datetime.now().date() - timedelta(days=days)
            start_date = end_date - timedelta(days=days)

            logs = db.query(DailyRunLog).filter(
                DailyRunLog.run_date >= start_date
            ).order_by(DailyRunLog.run_date.desc())

            results = []
            for log in logs:
                results.append({
                    "date": log.run_date,
                    "leads_found": log.leads_found,
                    "new_leads": log.new_leads,
                    "duplicates": log.duplicates_skipped,
                    "qualified": log.leads_qualified,
                    "flagged": log.leads_flagged,
                    "rejected": log.leads_rejected,
                    "emails_sent": log.emails_sent,
                    "runtime_seconds": log.runtime_seconds
                })

            return results

        except Exception as e:
            logger.error(f"Failed to get daily stats: {e}")
            return []

    def get_lead_by_id(self, lead_id: str, db: Session) -> Optional[Dict]:
        """Get a single lead by ID."""
        return db.query(Lead).filter(Lead.id == lead_id).first()

    def get_pending_leads(self, limit: int = 50, db: Session) -> List[Dict]:
        """Get pending leads that need manual review."""
        return db.query(Lead).filter(
            Lead.status == "pending",
            Lead.score >= 50
        ).order_by(Lead.score.desc()).limit(limit).all()

    def get_qualified_leads(self, db: Session) -> List[Dict]:
        """Get qualified leads ready for outreach."""
        return db.query(Lead).filter(
            Lead.qualification_status == "qualified",
            Lead.outreach_status == "not_started"
        ).order_by(Lead.score.desc()).all()

    def update_outreach_status(self, lead_id: str, step: int, db: Session) -> bool:
        """Update outreach status and step for a lead."""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.outreach_status = f"in_sequence"
            lead.email_sequence_step = step
            lead.last_email_date = datetime.now()
            lead.next_followup_date = self._calculate_next_date(step)
            db.commit()
            return True
        return False

    def _calculate_next_date(self, step: int) -> Optional[datetime]:
        """Calculate next follow-up date based on step number."""
        if step == 0:
            return datetime.now() + timedelta(days=0)

        timing = {
            1: timedelta(days=3),
            2: timedelta(days=7),
            3: timedelta(days=14),
            4: timedelta(days=100)  # Break-up
        }
        return timing.get(step)

    def cleanup_old_leads(self, days: int = 180, db: Session) -> int:
        """Mark old leads as cold (for monthly cleanup)."""
        cutoff_date = datetime.now() - timedelta(days=days)
        updated = db.query(Lead).filter(
            Lead.created_at < cutoff_date,
            Lead.outreach_status == "not_started"
        ).update({
            "status": "cold"
        })
        result = updated.rowcount
        db.commit()
        return result