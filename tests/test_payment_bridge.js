const assert = require("node:assert/strict");

let captured;
global.window = {
  fetch: async (input, init) => {
    captured = { input, init };
    return { ok: true };
  },
};

require("../frontend/sagpt-payments.js");

(async () => {
  const body = JSON.stringify({ priceId: "price_growth" });
  await window.fetch(
    "https://udoklrcatizfiuvrsg.supabase.co/functions/v1/create-checkout-session",
    {
      method: "POST",
      headers: { authorization: "Bearer public-anon-key", apikey: "public-anon-key" },
      body,
    },
  );

  assert.equal(
    captured.input,
    "https://sagpt-platform.onrender.com/api/payments/create-checkout-session",
  );
  assert.equal(captured.init.method, "POST");
  assert.equal(captured.init.headers["Content-Type"], "application/json");
  assert.equal(captured.init.body, body);

  await window.fetch("https://example.com/health", { method: "GET" });
  assert.equal(captured.input, "https://example.com/health");

  console.log("payment bridge tests passed");
})();
