- [ ] Fix Telegram sending errors by removing per-call event-loop creation
- [ ] Update `send_to_channel()` to use Telegram's synchronous API (or a single long-lived async loop)
- [ ] Re-run the script in `--dry-run` and then normal mode to verify no `Event loop is closed` errors
- [ ] Optionally improve retry/timeouts for external APIs (FMP/Benzinga) to reduce noise

