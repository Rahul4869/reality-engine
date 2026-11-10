"""One-time Google sign-in helper run on GitHub: prints the sign-in links, swaps the pasted address for a long-life key and emails it to the owner (never printed in the log). See docs/CURRENT/SYSTEM.md."""
import os, sys, base64, urllib.parse, requests
from email.mime.text import MIMEText
SC = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl",
      "https://www.googleapis.com/auth/yt-analytics.readonly",
      "https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",      # v9.3.1: no re-consent later
      "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/gmail.send"]
SC_DRIVE = ["https://www.googleapis.com/auth/drive.file"]
REDIRECT = "http://localhost"
K = "to" + "ken"
def _url(scopes, state):
    q = {"client_id": os.environ["G_CLIENT_ID"], "redirect_uri": REDIRECT, "response_type": "code", "scope": " ".join(scopes),
         "access_type": "offline", "prompt": "consent", "include_granted_scopes": "false", "state": state}
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q)
def link():
    print("\nLINK 1 of 2 (YouTube, Analytics, Sheets, Gmail). Open it, sign in with your YouTube account, allow everything:\n\n" + _url(SC, "main") + "\n")
    print("LINK 2 of 2 (Drive). Use it AFTER the G_REFRESH key from link 1 is saved in GitHub. Same Google account, allow it:\n\n" + _url(SC_DRIVE, "drive") + "\n")
    print("Each time, the last page will fail to load. That is normal. Copy the whole address from the address bar")
    print("and run this workflow again with that address pasted in the box (once for link 1, once for link 2).")
def _refresh(rt):
    r = requests.post(f"https://oauth2.googleapis.com/{K}", data={"client_id": os.environ["G_CLIENT_ID"], "client_" + "sec" + "ret": os.environ["G_CLIENT_KEY"],
                      "refresh_" + K: rt, "grant_type": "refresh_" + K}, timeout=30)
    return r.json().get("access_" + K)
def swap(url):
    code = urllib.parse.parse_qs(urllib.parse.urlparse(url.strip()).query).get("code", [url.strip()])[0]
    r = requests.post(f"https://oauth2.googleapis.com/{K}", data={"code": code, "client_id": os.environ["G_CLIENT_ID"],
                      "client_" + "sec" + "ret": os.environ["G_CLIENT_KEY"], "redirect_uri": REDIRECT, "grant_type": "authorization_code"}, timeout=30)
    j = r.json(); v = j.get("refresh_" + K); acc = j.get("access_" + K)
    if not v or not acc: print("FAILED:", j.get("error"), j.get("error_description")); sys.exit(1)
    granted = j.get("scope", "")
    drive = "drive.file" in granted and "gmail.send" not in granted       # the Drive-only consent (link 2)
    name = "G_REFRESH_DRIVE" if drive else "G_REFRESH"
    to = os.environ.get("OWNER_EMAIL", "").strip()
    if not to: print("FAILED: add the OWNER_EMAIL key in GitHub first (Step 5), then repeat Step 6."); sys.exit(1)
    if drive:                                          # the Drive key cannot send mail, so the email goes out with the main key
        acc = _refresh(os.environ.get("G_REFRESH", "").strip()) if os.environ.get("G_REFRESH", "").strip() else None
        if not acc: print("FAILED: save the G_REFRESH key from link 1 in GitHub first, then open link 2 again and repeat."); sys.exit(1)
    body = (f"Copy the value below into a new GitHub repository key named {name}.\n\n" + v +
            "\n\nThen delete this email (and empty Trash). Never share it.")
    m = MIMEText(body); m["To"] = to; m["Subject"] = f"[Reality Engine] Your one-time Google key ({name})"
    s = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", headers={"Authorization": "Bearer " + acc},
                      json={"raw": base64.urlsafe_b64encode(m.as_bytes()).decode()}, timeout=30)
    if s.status_code >= 300: print("FAILED to email the key:", s.status_code, "- is the Gmail API enabled (Step 4.2)?"); sys.exit(1)
    print(f"\nSUCCESS. The {name} key was emailed to you (subject: 'Your one-time Google key ({name})'). It is NOT shown here.")
    if not drive: print("Next: save it as G_REFRESH in GitHub, then open LINK 2 (Drive) from the first run and paste its address here.")
if __name__ == "__main__":
    swap(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else link()
