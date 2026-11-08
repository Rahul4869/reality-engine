# Making changes from your laptop with your own Claude subscription (no API money)

There are three ways a change reaches the pipeline. All end the same way: a pull request, automatic Checks, then your Merge tap.

| Way | When | Where Claude's work is paid from |
|---|---|---|
| **A. Phone** (dashboard / WhatsApp / email card → [Build it]) | Busy days | Claude Code in GitHub Actions on your Claude plan (`CC_OAUTH_TOKEN`); no API money |
| **B. Laptop + Claude desktop app (Claude Code)**: recommended when you have time | You want to discuss, watch and steer | Your Claude subscription usage |
| **C. Laptop + claude.ai chat + Claude in Chrome** | No Claude Code installed | Your Claude subscription usage |

## B. Claude desktop app → Code tab (recommended)
1. Install the Claude desktop app on your laptop (one time), open the **Code** tab and sign in with your Claude account.
2. Ask: "Clone my GitHub repo reality-engine and open it." Approve the GitHub sign-in when asked (you click Allow).
3. Paste the LAPTOP CHANGE PROMPT (`PROMPT_LAPTOP_CHANGE.md` in the pack), then describe the change in plain words.
4. Claude reads CLAUDE.md, discusses, builds on a branch, runs Plan Guard + the tests + the rehearsal, pushes the branch and opens a pull request.
5. GitHub Checks run. You tap **Merge** (email / dashboard / WhatsApp), or say "merge it" and click Merge yourself on the pull request page.

## C. claude.ai chat + Claude in Chrome (no install)
1. In a claude.ai chat (code execution + file creation + Claude in Chrome on), paste `PROMPT_LAPTOP_CHANGE.md` and describe the change.
2. Claude asks you to download the repo: GitHub → Code → Download ZIP. Upload it into the chat. Claude builds and tests it there (with `tools_sandbox/` if pytest is missing) and gives you a CHANGED zip.
3. With Claude in Chrome, Claude opens your repo's "Add file → Upload files" page on a new branch. You drag the unzipped files in and press **Commit changes** (your click). Claude opens the pull request page; you press **Create pull request**.
4. Checks run. Tap **Merge** when they are green.

## Rules that always apply
- One change at a time; never two chats building at once.
- You sign in and press final buttons yourself. Claude never handles passwords or secret keys.
- If the Checks fail, nothing reaches the channel. Claude fixes on the same branch or you press Reject.
