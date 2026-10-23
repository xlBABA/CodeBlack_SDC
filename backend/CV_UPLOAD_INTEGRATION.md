# CV upload integration — for Mohammad (Milestone 11B)

Covers `POST /api/v1/cv/parse`: PDF upload → local text extraction → RunPod GLM-5.3 → a **draft** for the user to review and confirm. Nothing here writes to the stored profile — that still only happens when you submit to the existing `POST /profile/analyze`, unchanged.

## 1. Endpoint and multipart request

```
POST /api/v1/cv/parse
Content-Type: multipart/form-data
```

Single form field, `file`, a PDF, max **5 MB**.

```js
const form = new FormData()
form.append('file', pdfFile) // a File/Blob from an <input type="file" accept="application/pdf">
const res = await fetch('/api/v1/cv/parse', { method: 'POST', body: form })
```

No JSON body, no other fields. No auth header beyond whatever your app already sends.

## 2. Success response — `data.status: "ok"`

```json
{
  "data": {
    "status": "ok",
    "page_count": 1,
    "extracted_text_preview": null,
    "draft": {
      "name": "Jane Student",
      "summary": "CS undergraduate",
      "education": [
        { "institution": "Test University", "degree": "BSc", "field_of_study": "Computer Science", "start_date": null, "end_date": null }
      ],
      "mapped_skills": [
        { "skill_id": "python", "name": "Python", "raw_text": "Python" },
        { "skill_id": "sql", "name": "SQL", "raw_text": "SQL" }
      ],
      "unmapped_skills": [
        { "raw_text": "Underwater Basket Weaving" }
      ],
      "projects": [
        { "title": "Sales dashboard", "description": "Built with SQL and Python" }
      ],
      "experience": [],
      "certifications": [],
      "suggested_profile": {
        "profile_id": null,
        "education_level": null,
        "degree": "Computer Science",
        "semester": null,
        "target_role_id": null,
        "interests": [],
        "skills": [
          { "skill_id": "python", "name": "Python", "proficiency": null },
          { "skill_id": "sql", "name": "SQL", "proficiency": null }
        ],
        "projects": ["Sales dashboard: Built with SQL and Python"],
        "experience_summary": "CS undergraduate"
      }
    }
  },
  "data_mode": "live",
  "generated_at": "2026-10-23T04:19:08Z",
  "warnings": [
    "Extracted automatically; please review every field before confirming — nothing here is final.",
    "1 skill(s) were not recognized against the current catalogue and were not added to your profile automatically; review them below."
  ]
}
```

**Everything in `draft` is for display/editing.** `draft.suggested_profile` is the one field shaped exactly like `POST /profile/analyze`'s request body — a sensible pre-filled default, not an authoritative result.

## 3. Fallback states — `data.status` is not always `"ok"`

| `status` | When | What you get |
|---|---|---|
| `"ok"` | GLM extracted successfully | Full `draft` above, `extracted_text_preview: null` |
| `"no_extractable_text"` | PDF has no selectable text (likely scanned/image-only) — **no OCR is performed** | Empty `draft` (all fields null/empty), a warning telling the user to fill in manually |
| `"manual_review"` | GLM was unreachable, timed out, or returned something unusable | Empty `draft`, plus `extracted_text_preview` — the **first 500 characters** of the raw extracted text (never the whole document), so the user can copy from it manually |

**Nothing is ever fabricated.** If extraction fails in any way, you get an honestly empty draft, never guessed data.

## 4. Error responses

| HTTP | `error.code` | Cause |
|---|---|---|
| 422 | `INVALID_CV_FILE` | Empty file, not a PDF, corrupted PDF, password-protected PDF, or a declared Content-Type that's clearly not a PDF (e.g. `image/png`) — `error.message` says which |
| 413 | `FILE_TOO_LARGE` | Over the 5 MB cap |
| 422 | `VALIDATION_ERROR` | Missing the `file` field entirely |

```json
{ "error": { "code": "INVALID_CV_FILE", "message": "This PDF is password-protected. Please upload an unprotected PDF.", "details": null }, "request_id": "..." }
```

## 5. Suggested UI states

1. **Idle** — file picker, "PDF only, max 5 MB" hint.
2. **Loading** — while the request is in flight (GLM calls can take several seconds; there's no streaming, it's one request/one response).
3. **Review (status "ok")** — an editable form pre-filled from `draft`, split into:
   - Confirmed fields (from `suggested_profile`) — editable before submit.
   - **Unmapped skills** (`draft.unmapped_skills`) — show these separately with an "add anyway" or "ignore" choice; they are not in `suggested_profile.skills` yet.
   - Everything else extracted (`education`, `projects`, `experience`, `certifications`, `name`, `summary`) — shown for context/copy-paste into other fields, since only `suggested_profile`'s shape is what the matching system actually consumes today.
4. **Manual review (status "manual_review" or "no_extractable_text")** — show the relevant warning text verbatim, and (for `manual_review`) the `extracted_text_preview` in a read-only text box the user can copy from, then route to the normal manual intake form.
5. **Error** — show `error.message` directly; it's already written to be user-facing.

## 6. Confirmation and matching handoff

No new submit endpoint. Once the user is happy with the (possibly edited) draft:

```js
await fetch('/api/v1/profile/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(editedSuggestedProfile), // same shape as draft.suggested_profile
})
```

This is the exact same call your intake form already makes — `/cv/parse` only gets you a pre-filled starting point for it. From there, `/careers/match`, `/roadmaps/generate`, etc. all work exactly as before, unchanged.

## Known limitations (for your UI copy)

- No OCR — a scanned/photographed CV will always come back as `"no_extractable_text"`.
- `education_level` (undergraduate/graduate) is never auto-filled — the CV's degree text doesn't map cleanly to that field without guessing, so it's left for the user.
- Only one PDF per request; no batch upload.
