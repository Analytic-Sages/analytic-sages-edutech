#!/usr/bin/env python3
"""Unpublish every published Insights article except one (ops helper).

AI-generated backfill articles are being taken down from the public site, keeping
only the manually-written research post live. This does not delete anything — it
flips status back to draft, exactly like clicking "Unpublish" in the editor. Articles
can be republished individually later from /admin/insights.

Usage (from backend/, with DATABASE_URL pointed at the target environment):
  python scripts/unpublish_other_insights.py --keep-slug <slug> --dry-run
  python scripts/unpublish_other_insights.py --keep-slug <slug>
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.article import Article, ArticleStatus


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-slug", required=True, help="Slug of the article to leave published")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        keep = db.scalar(select(Article).where(Article.slug == args.keep_slug))
        if not keep:
            print(f"No article found with slug: {args.keep_slug}")
            sys.exit(1)
        if keep.status != ArticleStatus.PUBLISHED:
            print(f"Warning: {keep.slug} is not currently published (status={keep.status.value})")

        others = db.scalars(
            select(Article).where(Article.status == ArticleStatus.PUBLISHED, Article.id != keep.id)
        ).all()

        if not others:
            print("No other published articles found. Nothing to do.")
            return

        print(f"Keeping published: {keep.title!r} ({keep.slug})")
        print(f"Unpublishing {len(others)} article(s):")
        for article in others:
            print(f"  - {article.title!r} ({article.slug})")

        if args.dry_run:
            print("\nDry run: no changes saved. Re-run without --dry-run to apply.")
            return

        for article in others:
            article.status = ArticleStatus.DRAFT
        db.commit()
        print("\nDone. Those articles are now drafts and no longer visible on the public site.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
