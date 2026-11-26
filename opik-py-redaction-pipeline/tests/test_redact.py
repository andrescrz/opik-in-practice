from redact import apply_findings, leaked, parse_json_object, regex_redact, regex_rescan


def test_regex_pass_masks_structured_pii():
    text, counts = regex_redact("Mail a@b.test, call (555) 014-2290, SSN 000-12-3456, MRN-482113, DOB 03/14/1987")
    assert text == "Mail [EMAIL], call [PHONE], SSN [SSN], [ID], DOB [DOB]"
    assert counts == {"EMAIL": 1, "SSN": 1, "PHONE": 1, "ID": 1, "DOB": 1}


def test_regex_rescan_ignores_placeholders():
    assert regex_rescan("Call [PHONE] or 555-019-7731") == ["555-019-7731"]


def test_findings_longest_first_and_typed():
    text, masked = apply_findings(
        "Daniel A. Okonkwo met Daniel", [{"text": "Daniel", "type": "name"}, {"text": "Daniel A. Okonkwo", "type": "NAME"}]
    )
    assert text == "[NAME] met [NAME]"
    assert masked == 2


def test_findings_skip_placeholders_and_sentence_length_spans():
    doc = "Dear [NAME], the heating is out and nobody has answered my three letters about it this week."
    findings = ["[NAME]", doc, "heating"]
    text, masked = apply_findings(doc, findings)
    assert masked == 1
    assert "[NAME]" in text and "[REDACTED] is out" in text


def test_leaked_counts_only_planted_strings_still_present():
    assert leaked("Hello [NAME] from 9 Orchard Mews", ["9 Orchard Mews", "Tomasz"]) == ["9 Orchard Mews"]


def test_parse_json_object_strips_code_fences():
    assert parse_json_object('```json\n{"findings": []}\n```') == {"findings": []}
