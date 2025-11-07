# # fetch_congress_bills.py
# # requirements: httpx, python-dotenv (pip install httpx python-dotenv)

# import os
# import asyncio
# from typing import AsyncIterator, Dict, Any, List
# import httpx
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv('api.env')

# API_KEY = os.getenv("CONGRESS_API_KEY")
# BASE = "https://api.congress.gov/v3"


# # --------- low-level helpers ---------
# async def _get_json(client: httpx.AsyncClient, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
#     params = {"api_key": API_KEY, "format": "json", **params}
#     r = await client.get(url, params=params, timeout=30)
#     r.raise_for_status()
#     return r.json()


# async def _paginate(client: httpx.AsyncClient, url: str, params: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
#     """Iterate through paginated v3 results (follows 'pagination.next' links when present)."""
#     data = await _get_json(client, url, params)
#     yield data
#     # The API returns a 'pagination' object with 'next' url when more data exist.
#     while True:
#         pagination = data.get("pagination") or {}
#         next_url = pagination.get("next")
#         if not next_url:
#             break
#         # next_url already includes api_key/format; no extra params needed
#         data = await _get_json(client, next_url, {})
#         yield data


# async def fetch_bill_summary(client: httpx.AsyncClient, congress: int, bill_type: str, bill_number: int) -> str:
#     """
#     Fetch the summary text for a specific bill.
#     Returns the most recent summary text, or empty string if none available.
#     """
#     try:
#         data = await _get_json(
#             client,
#             f"{BASE}/bill/{congress}/{bill_type.lower()}/{bill_number}/summaries",
#             {}
#         )
#         summaries = data.get("summaries", [])
#         if summaries:
#             # Get the most recent summary
#             latest_summary = summaries[0]
#             return (latest_summary.get("text") or "").strip()
#         return ""
#     except Exception as e:
#         print(f"Warning: Could not fetch summary for {bill_type} {bill_number}: {e}")
#         return ""


# # --------- main fetchers ---------
# async def fetch_enacted_laws(congress: int, limit: int = 50, include_summaries: bool = False) -> List[Dict[str, Any]]:
#     """
#     Fetch enacted public laws for a specific Congress.
#     This uses the /law endpoint which is much faster than searching through all bills.
    
#     Args:
#         congress: Congress number (e.g., 119)
#         limit: Maximum number of laws to return
#         include_summaries: If True, fetch full summaries for each law (slower)
#     """
#     if not API_KEY:
#         raise RuntimeError("CONGRESS_API_KEY not found. Make sure you have api.env with CONGRESS_API_KEY=your_key")
    
#     results: List[Dict[str, Any]] = []
#     async with httpx.AsyncClient() as client:
#         print(f"Fetching enacted laws from {congress}th Congress...")
#         async for page in _paginate(
#             client,
#             f"{BASE}/law/{congress}",
#             {"limit": 250}
#         ):
#             bills = page.get("bills", [])
#             for row in bills:
#                 latest = row.get("latestAction") or {}
#                 laws = row.get("laws", [])
#                 law_info = laws[0] if laws else {}
                
#                 bill_type = row.get("type", "").lower()
#                 bill_number = row.get("number")
                
#                 bill_data = {
#                     "bill_id": f"{row.get('type')} {bill_number}",
#                     "congress": row.get("congress"),
#                     "title": (row.get("title") or "").strip(),
#                     "public_law_number": law_info.get("number"),
#                     "law_type": law_info.get("type"),
#                     "enacted_date": latest.get("actionDate"),
#                     "latest_action": latest.get("text"),
#                     "bill_url": row.get("url"),
#                 }
                
#                 # Fetch summary if requested
#                 if include_summaries:
#                     summary = await fetch_bill_summary(client, congress, bill_type, bill_number)
#                     bill_data["summary"] = summary
                
#                 results.append(bill_data)
#                 print(f"  Found: {bill_data['bill_id']} - Public Law {bill_data['public_law_number']}")
                
#                 if len(results) >= limit:
#                     return results
        
#         print(f"Total enacted laws found: {len(results)}")
#         return results


# async def fetch_recent_bills(congress: int, bill_type: str = None, limit: int = 50, include_summaries: bool = False) -> List[Dict[str, Any]]:
#     """
#     Get recent bills from Congress, sorted by latest action date.
    
#     Args:
#         congress: Congress number (e.g., 119 for current)
#         bill_type: Optional filter - 'hr', 's', 'hjres', 'sjres', etc. If None, fetches all types.
#         limit: Maximum number of bills to return
#         include_summaries: If True, fetch full summaries for each bill (slower)
#     """
#     if not API_KEY:
#         raise RuntimeError("CONGRESS_API_KEY not found. Make sure you have api.env with CONGRESS_API_KEY=your_key")

#     results: List[Dict[str, Any]] = []
#     async with httpx.AsyncClient() as client:
#         if bill_type:
#             # Fetch specific bill type
#             bill_types = [bill_type.lower()]
#         else:
#             # Fetch all major bill types
#             bill_types = ["hr", "s", "hjres", "sjres"]
        
#         for btype in bill_types:
#             async for page in _paginate(
#                 client,
#                 f"{BASE}/bill/{congress}/{btype}",
#                 {
#                     "sort": "updateDate:desc",  # most recently updated first
#                     "limit": 250,
#                 },
#             ):
#                 bills = page.get("bills", []) or []
#                 for row in bills:
#                     latest = row.get("latestAction") or {}
#                     bill_data = {
#                         "bill_id": f"{btype.upper()} {row.get('number')}",
#                         "congress": row.get("congress"),
#                         "title": (row.get("title") or "").strip(),
#                         "latest_action": latest.get("text"),
#                         "latest_action_date": latest.get("actionDate"),
#                         "update_date": row.get("updateDate"),
#                         "bill_type": row.get("type"),
#                         "bill_url": row.get("url"),
#                     }
                    
#                     # Fetch summary if requested
#                     if include_summaries:
#                         summary = await fetch_bill_summary(client, congress, btype, row.get('number'))
#                         bill_data["summary"] = summary
                    
#                     results.append(bill_data)
#                     if len(results) >= limit:
#                         return results
#     return results


# async def fetch_bills_by_status(congress: int, status_keyword: str, limit: int = 50, include_summaries: bool = False) -> List[Dict[str, Any]]:
#     """
#     Get bills filtered by status keyword in their latest action.
    
#     Common keywords:
#     - "passed" - bills that passed one or both chambers
#     - "president" - bills sent to the president
#     - "became public law" - enacted bills
#     - "committee" - bills in committee
    
#     Args:
#         congress: Congress number
#         status_keyword: Keyword to search for in latest action
#         limit: Maximum number of bills to return
#         include_summaries: If True, fetch full summaries for each bill (slower)
#     """
#     if not API_KEY:
#         raise RuntimeError("CONGRESS_API_KEY not found. Make sure you have api.env with CONGRESS_API_KEY=your_key")

#     out: List[Dict[str, Any]] = []
#     async with httpx.AsyncClient() as client:
#         bill_types = ["hr", "s", "hjres", "sjres"]
#         checked = 0
#         max_to_check = 2000  # Stop after checking this many bills total
        
#         for btype in bill_types:
#             if len(out) >= limit:
#                 break
                
#             print(f"Searching {btype.upper()} bills for '{status_keyword}'...")
#             async for page in _paginate(
#                 client,
#                 f"{BASE}/bill/{congress}/{btype}",
#                 {
#                     "sort": "updateDate:desc",
#                     "limit": 250,
#                 },
#             ):
#                 bills = page.get("bills", []) or []
#                 for row in bills:
#                     checked += 1
#                     if checked > max_to_check:
#                         print(f"Searched {checked} bills, found {len(out)} matching.")
#                         return out
                    
#                     latest = row.get("latestAction") or {}
#                     action_text = (latest.get("text") or "").lower()
                    
#                     if status_keyword.lower() in action_text:
#                         print(f"  Found: {btype.upper()} {row.get('number')}")
#                         bill_data = {
#                             "bill_id": f"{btype.upper()} {row.get('number')}",
#                             "congress": row.get("congress"),
#                             "title": (row.get("title") or "").strip(),
#                             "latest_action": latest.get("text"),
#                             "latest_action_date": latest.get("actionDate"),
#                             "bill_url": row.get("url"),
#                         }
                        
#                         # Fetch summary if requested
#                         if include_summaries:
#                             summary = await fetch_bill_summary(client, congress, btype, row.get('number'))
#                             bill_data["summary"] = summary
                        
#                         out.append(bill_data)
#                         if len(out) >= limit:
#                             print(f"Found {limit} bills matching '{status_keyword}'")
#                             return out
                
#                 # Check if we should stop early for this bill type
#                 if checked % 250 == 0:
#                     print(f"  Checked {checked} bills so far, found {len(out)}...")
                    
#     print(f"Finished searching. Checked {checked} bills, found {len(out)} matching.")
#     return out


# # --------- convenience runner ---------
# if __name__ == "__main__":
#     import json
#     import argparse

#     parser = argparse.ArgumentParser(description="Fetch bills from Congress.gov API")
#     parser.add_argument("--congress", type=int, default=119, help="Congress number (e.g., 119 for 2025-2026)")
#     parser.add_argument("--limit", type=int, default=20, help="Number of bills to fetch")
#     parser.add_argument("--type", type=str, help="Bill type: hr, s, hjres, sjres (default: all)")
#     parser.add_argument("--status", type=str, help="Filter by status keyword (e.g., 'president', 'passed')")
#     parser.add_argument("--laws", action="store_true", help="Fetch enacted public laws (fast)")
#     parser.add_argument("--summaries", action="store_true", help="Include bill summaries (slower)")
#     args = parser.parse_args()

#     async def main():
#         print(f"Fetching bills from {args.congress}th Congress...\n")
        
#         if args.laws:
#             bills = await fetch_enacted_laws(args.congress, limit=args.limit, include_summaries=args.summaries)
#             print(f"\n# Enacted Public Laws")
#         elif args.status:
#             bills = await fetch_bills_by_status(args.congress, args.status, limit=args.limit, include_summaries=args.summaries)
#             print(f"\n# Bills with status containing '{args.status}'")
#         else:
#             bills = await fetch_recent_bills(args.congress, bill_type=args.type, limit=args.limit, include_summaries=args.summaries)
#             print(f"\n# Recent bills" + (f" (type: {args.type})" if args.type else ""))
        
#         print(json.dumps(bills, indent=2))
#         print(f"\nTotal: {len(bills)} bills")

#     asyncio.run(main())