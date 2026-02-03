from __future__ import annotations

import argparse
import datetime
from typing import Any

import environ
import things

from opentasks.cloud import CloudAPI, HistoryResponse
from opentasks.models import StartType, Status, TaskType
from opentasks.parser import State, StateBuilder

START_TYPE_MAP: dict[StartType, str] = {
    StartType.NOT_STARTED: "Inbox",
    StartType.ANYTIME: "Anytime",
    StartType.SOMEDAY: "Someday",
}

STATUS_MAP: dict[Status, str] = {
    Status.OPEN: "incomplete",
    Status.CANCELLED: "canceled",
    Status.COMPLETED: "completed",
}

TASK_TYPE_MAP: dict[TaskType, str] = {
    TaskType.TASK: "to-do",
    TaskType.HEADING: "heading",
    TaskType.PROJECT: "project",
}


def _ts_to_date(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime(
        "%Y-%m-%d"
    )


def _ts_to_datetime(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def load_cloud_state_from_files() -> State:
    builder = StateBuilder()
    files = [
        "history_0.json",
        "history_2500.json",
        "history_5000.json",
        "history_6051.json",
    ]
    for fname in files:
        with open(fname) as f:
            data = f.read()
        resp = HistoryResponse.from_json(data)
        builder.apply(resp)
    return builder.build()


def load_cloud_state_from_api() -> State:
    env = environ.Env()
    environ.Env.read_env("src/.env")
    api = CloudAPI(env.str("THINGS_EMAIL"), env.str("THINGS_PASSWORD"))
    api.login()
    return api.full_state()


def compare_uuids(state: State) -> None:
    local_tasks: list[dict[str, Any]] = things.tasks(status=None)
    local_trashed: list[dict[str, Any]] = things.tasks(status=None, trashed=True)
    local_all = local_tasks + local_trashed

    local_uuids = {t["uuid"] for t in local_all}
    cloud_task_uuids = set(state.tasks.keys())

    only_cloud = cloud_task_uuids - local_uuids
    only_local = local_uuids - cloud_task_uuids
    common = cloud_task_uuids & local_uuids

    print("=" * 60)
    print("UUID COMPARISON (Tasks + Projects + Headings)")
    print("=" * 60)
    print(f"Cloud tasks:  {len(cloud_task_uuids)}")
    print(f"Local tasks:  {len(local_uuids)}")
    print(f"Common:       {len(common)}")
    print(f"Only cloud:   {len(only_cloud)}")
    print(f"Only local:   {len(only_local)}")

    if only_cloud:
        print("\n  Cloud-only (first 10):")
        for uid in list(only_cloud)[:10]:
            t = state.tasks[uid]
            print(
                f"    {uid[:12]} | {TASK_TYPE_MAP.get(t.task_type, '?'):8} | "
                f"{STATUS_MAP.get(t.status, '?'):11} | "
                f"trashed={t.trashed} | {t.title[:50]}"
            )

    if only_local:
        print("\n  Local-only (first 10):")
        local_by_uuid = {t["uuid"]: t for t in local_all}
        for uid in list(only_local)[:10]:
            t = local_by_uuid[uid]
            print(
                f"    {uid[:12]} | {t['type']:8} | {t['status']:11} | {t['title'][:50]}"
            )


def compare_fields(state: State) -> None:
    local_tasks: list[dict[str, Any]] = things.tasks(status=None)
    local_trashed: list[dict[str, Any]] = things.tasks(status=None, trashed=True)
    local_by_uuid = {t["uuid"]: t for t in local_tasks + local_trashed}

    mismatches: dict[str, int] = {}
    mismatch_examples: dict[str, list[str]] = {}
    compared = 0

    for uid, cloud_task in state.tasks.items():
        local_task = local_by_uuid.get(uid)
        if local_task is None:
            continue

        compared += 1
        cloud_notes = (cloud_task.notes.value if cloud_task.notes else "").strip()
        local_notes = (local_task.get("notes") or "").strip()

        checks = [
            ("title", cloud_task.title, local_task["title"]),
            ("type", TASK_TYPE_MAP.get(cloud_task.task_type), local_task["type"]),
            ("status", STATUS_MAP.get(cloud_task.status), local_task["status"]),
            (
                "start",
                START_TYPE_MAP.get(cloud_task.start_type),
                local_task.get("start"),
            ),
            ("deadline", _ts_to_date(cloud_task.deadline), local_task.get("deadline")),
            (
                "start_date",
                _ts_to_date(cloud_task.start_date),
                local_task.get("start_date"),
            ),
            ("notes", cloud_notes or None, local_notes or None),
        ]

        for field_name, cloud_val, local_val in checks:
            cloud_norm = cloud_val if cloud_val else None
            local_norm = local_val if local_val else None
            if cloud_norm != local_norm:
                mismatches[field_name] = mismatches.get(field_name, 0) + 1
                if len(mismatch_examples.get(field_name, [])) < 3:
                    mismatch_examples.setdefault(field_name, []).append(
                        f"    {uid[:12]} | cloud={cloud_norm!r} vs local={local_norm!r}"
                        f" | title={cloud_task.title[:40]}"
                    )

    print("\n" + "=" * 60)
    print("FIELD COMPARISON")
    print("=" * 60)
    print(f"Tasks compared: {compared}")

    if not mismatches:
        print("All fields match!")
    else:
        print("\nMismatches by field:")
        for field_name, count in sorted(mismatches.items(), key=lambda x: -x[1]):
            pct = count / compared * 100
            print(f"  {field_name:15} {count:5} mismatches ({pct:.1f}%)")
            for ex in mismatch_examples.get(field_name, []):
                print(ex)


def compare_areas(state: State) -> None:
    local_areas: list[dict[str, Any]] = things.areas()
    local_by_uuid = {a["uuid"]: a for a in local_areas}
    cloud_uuids = set(state.areas.keys())
    local_uuids = set(local_by_uuid.keys())

    print("\n" + "=" * 60)
    print("AREAS")
    print("=" * 60)
    print(f"Cloud: {len(cloud_uuids)}, Local: {len(local_uuids)}")
    print(f"Only cloud: {cloud_uuids - local_uuids}")
    print(f"Only local: {local_uuids - cloud_uuids}")

    for uid in cloud_uuids & local_uuids:
        cloud_a = state.areas[uid]
        local_a = local_by_uuid[uid]
        if cloud_a.title != local_a["title"]:
            print(
                f"  Title mismatch {uid[:12]}: {cloud_a.title!r} vs {local_a['title']!r}"
            )


def compare_tags(state: State) -> None:
    local_tags: list[dict[str, Any]] = things.tags()
    local_by_uuid = {t["uuid"]: t for t in local_tags}
    cloud_uuids = set(state.tags.keys())
    local_uuids = set(local_by_uuid.keys())

    print("\n" + "=" * 60)
    print("TAGS")
    print("=" * 60)
    print(f"Cloud: {len(cloud_uuids)}, Local: {len(local_uuids)}")
    print(f"Only cloud: {cloud_uuids - local_uuids}")
    print(f"Only local: {local_uuids - cloud_uuids}")

    for uid in cloud_uuids & local_uuids:
        cloud_t = state.tags[uid]
        local_t = local_by_uuid[uid]
        if cloud_t.title != local_t["title"]:
            print(
                f"  Title mismatch {uid[:12]}: {cloud_t.title!r} vs {local_t['title']!r}"
            )


def compare_checklist_items(state: State) -> None:
    cloud_items = state.checklist_items
    total_checked = 0
    total_mismatches = 0

    local_tasks: list[dict[str, Any]] = things.tasks(status=None)
    for local_task in local_tasks:
        if not local_task.get("checklist"):
            continue
        local_checklist: list[dict[str, Any]] = things.checklist_items(
            local_task["uuid"]
        )
        cloud_checklist = state.checklist_for_task(local_task["uuid"])
        cloud_by_uuid = {c.uuid: c for c in cloud_checklist}
        local_by_uuid = {c["uuid"]: c for c in local_checklist}

        for uid, local_c in local_by_uuid.items():
            total_checked += 1
            cloud_c = cloud_by_uuid.get(uid)
            if cloud_c is None:
                total_mismatches += 1
                continue
            if cloud_c.title != local_c["title"]:
                total_mismatches += 1

    print("\n" + "=" * 60)
    print("CHECKLIST ITEMS")
    print("=" * 60)
    print(f"Cloud total: {len(cloud_items)}")
    print(f"Local checked: {total_checked}")
    print(f"Mismatches: {total_mismatches}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch latest history from Things Cloud API instead of local JSON files",
    )
    args = parser.parse_args()

    if args.live:
        print("Fetching latest history from Things Cloud API...")
        state = load_cloud_state_from_api()
    else:
        state = load_cloud_state_from_files()

    compare_uuids(state)
    compare_fields(state)
    compare_areas(state)
    compare_tags(state)
    compare_checklist_items(state)
