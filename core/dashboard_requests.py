"""One simple, sorted list of a client's repair tickets and part requests for the dashboard."""

GROUP_PRIORITY = {"action": 0, "active": 1, "done": 2}

# status -> (label, colour tone, stage 1-3, group)
REPAIR_STATUS = {
    "pending": ("Received", "amber", 1, "active"),
    "quoted": ("Quoted", "sky", 1, "active"),
    "in_progress": ("In progress", "orange", 2, "active"),
    "completed": ("Ready for collection", "green", 3, "done"),
    "no_fix": ("No-fix", "slate", 3, "done"),
    "cancelled": ("Cancelled", "slate", 3, "done"),
}
PART_STATUS = {
    "pending": ("Received", "amber", 1, "active"),
    "quoted": ("Quoted", "sky", 1, "active"),
    "in_progress": ("Sourcing", "orange", 2, "active"),
    "fulfilled": ("Ready", "green", 3, "done"),
    "declined": ("Unavailable", "slate", 3, "done"),
}


def _describe(status, quote_status, table, quote_label):
    label, tone, stage, group = table.get(status, (str(status).replace("_", " ").title(), "slate", 1, "active"))
    if status == "quoted" and quote_status == "sent":
        return quote_label, "blue", stage, "action"
    if status == "quoted" and quote_status == "declined":
        label = "Quote declined"
    return label, tone, stage, group


def _message_count(obj):
    # messages are prefetched by the dashboard view, so this does not query per row
    return len(obj.messages.all())


def build_client_requests(tickets, part_requests):
    rows = []
    for t in tickets:
        label, tone, stage, group = _describe(t.status, t.quote_status, REPAIR_STATUS, "Quote ready: needs your approval")
        title = t.device
        subtitle = " ".join(filter(None, [t.manufacturer, t.get_device_category_display()]))
        rows.append({
            "kind": "repair", "obj_id": t.id, "ref": t.ticket_id, "title": title, "subtitle": subtitle,
            "extra": t.get_logistics_preference_display() if t.logistics_preference else "",
            "quoted_price": t.quoted_price, "status_label": label, "tone": tone, "stage": stage, "group": group,
            "image_url": t.diagnostic_image.url if t.diagnostic_image else "",
            "created_at": t.created_at, "message_count": _message_count(t),
            "search": " ".join([t.ticket_id or "", title, subtitle, label]).lower(),
        })
    for p in part_requests:
        label, tone, stage, group = _describe(p.status, p.quote_status, PART_STATUS, "Quote ready: needs your approval")
        title = p.part_needed
        subtitle = p.device_model
        rows.append({
            "kind": "part", "obj_id": p.id, "ref": p.request_id, "title": title, "subtitle": subtitle,
            "extra": p.get_condition_preference_display() if p.condition_preference else "",
            "quoted_price": p.quoted_price, "status_label": label, "tone": tone, "stage": stage, "group": group,
            "image_url": "",
            "created_at": p.created_at, "message_count": _message_count(p),
            "search": " ".join([p.request_id or "", title, subtitle, label]).lower(),
        })
    rows.sort(key=lambda r: (GROUP_PRIORITY[r["group"]], -r["created_at"].timestamp()))
    counts = {"all": len(rows), "action": 0, "active": 0, "done": 0, "repair": 0, "part": 0}
    for r in rows:
        counts[r["group"]] += 1
        counts[r["kind"]] += 1
    return rows, counts
