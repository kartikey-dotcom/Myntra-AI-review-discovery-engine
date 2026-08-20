from src.services.corpus_analytics import CorpusAnalyticsEngine

print("=== ACCEPTANCE CHECK 1: WISHLIST DELIBERATION CLAIMS ===")
findings = CorpusAnalyticsEngine.get_verified_findings(limit=100)
rejected = CorpusAnalyticsEngine.get_rejected_log(limit=100)

print("\n[VERIFIED WISHLIST DELIBERATION CLAIMS & QUOTES]:")
for f in [x for x in findings if x['category'] == 'wishlist_behavior'][:3]:
    print(f"Claim: '{f['claim_text']}'")
    print(f"Quote: '{f['quote']}'")
    print(f"Platform: {f['source_platform']} | Record ID: {f['review_id']}\n")

print("\n[REJECTED MISMATCHED PRICE QUOTES IN WISHLIST_BEHAVIOR]:")
for r in [x for x in rejected if x['category'] == 'wishlist_behavior'][:3]:
    print(f"Claim: '{r['claim_text']}'")
    print(f"Quote: '{r['quote']}'")
    print(f"Rejection Reason: {r['rejection_reason']}")
    print(f"Platform: {r['source_platform']} | Record ID: {r['review_id']}\n")

print("\n=== ACCEPTANCE CHECK 3: SPOT CHECK 5 CATEGORIES ===")
categories = ["price_behavior", "size_fit_uncertainty", "return_refund", "styling_occasion", "comparison_shopping"]
for cat in categories:
    match = next(x for x in findings if x['category'] == cat)
    print(f"Category: {cat}")
    print(f"Claim: '{match['claim_text']}'")
    print(f"Quote: '{match['quote']}'")
    print(f"Platform: {match['source_platform']} | Record ID: {match['review_id']}\n")
