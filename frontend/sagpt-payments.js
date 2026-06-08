/**
 * Redirect the retired Supabase Checkout function to the SAGPT payment API.
 */
(function () {
  "use strict";

  var retiredCheckoutUrl =
    "https://udoklrcatizfiuvrsg.supabase.co/functions/v1/create-checkout-session";
  var checkoutApiUrl =
    "https://sagpt-platform.onrender.com/api/payments/create-checkout-session";
  var originalFetch = window.fetch.bind(window);

  window.fetch = function (input, init) {
    var url = typeof input === "string" ? input : input && input.url;

    if (url === retiredCheckoutUrl) {
      var options = init || {};
      return originalFetch(checkoutApiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: options.body,
        signal: options.signal,
      });
    }

    return originalFetch(input, init);
  };
})();
