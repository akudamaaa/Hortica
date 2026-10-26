from functools import lru_cache
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse, reverse_lazy


@lru_cache(maxsize=1)
def legacy_pages():
    source = Path(settings.BASE_DIR) / "pages" / "data" / "legacy_content.json"
    return {page["key"]: page for page in json.loads(source.read_text(encoding="utf-8"))}


CORE_PAGES = {"home", "project", "history", "crew", "track", "coordinates"}
PAGE_URLS = {
    "home": "home", "project": "project", "history": "history", "crew": "crew",
    "track": "voyages", "coordinates": "coordinates", "oldspice": "oldspice",
    "2006": "voyage-2006", "2007": "voyage-2007", "2009": "voyage-2009", "2010": "voyage-2010",
}
PAGE_PATHS = {
    "/": "home", "/index.htm": "home", "/project.htm": "project", "/project/": "project",
    "/history.htm": "history", "/history/": "history", "/crew.htm": "crew", "/crew/": "crew",
    "/track.htm": "track", "/voyages/": "track", "/koord.htm": "coordinates",
    "/coordinates/": "coordinates", "/oldspice.htm": "oldspice", "/2006.htm": "2006",
    "/2007.htm": "2007", "/2009.htm": "2009", "/2010.htm": "2010",
}
OLD_CREW_ROTATION = (
    "001", "005", "006", "007", "008", "009", "010", "011", "012", "016", "017", "018",
    "020", "021", "025", "027", "029", "034", "037", "038", "046", "047", "053", "057", "058", "059",
)


def source_link(page, part):
    """Resolve a cached source link to a local route or a copied static asset."""
    absolute = urljoin(page["source"], part.get("href", ""))
    parsed = urlparse(absolute)
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    if parsed.netloc.lower() in {"www.xortica.ru", "xortica.ru"}:
        target = PAGE_PATHS.get(parsed.path.lower())
        if target in PAGE_URLS:
            return reverse(PAGE_URLS[target]) + fragment
        if parsed.path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")):
            for image in page.get("images", []):
                source_path = urlparse(urljoin(page["source"], image.get("src", ""))).path.lower()
                full_path = urlparse(urljoin(page["source"], image.get("full", ""))).path.lower()
                if parsed.path.lower() in {source_path, full_path}:
                    return static(image.get("full") or image["src"])
            filename = Path(parsed.path).name
            for asset in Path(settings.BASE_DIR, "assets", "legacy").rglob(filename):
                relative = asset.relative_to(Path(settings.BASE_DIR, "assets")).as_posix()
                return static(relative)
        return ""
    if parsed.scheme in {"http", "https", "mailto"}:
        return absolute
    return ""


def legacy_page(request, key):
    original = legacy_pages().get(key)
    if original is None:
        raise Http404
    page = dict(original)
    page["blocks"] = [dict(block) for block in original.get("blocks", [])]
    for block in page["blocks"]:
        for part in block.get("parts", []):
            if part.get("type") == "link":
                part["resolved_href"] = source_link(original, part)
    page["images"] = [image for image in original.get("images", []) if image.get("src")]
    if key == "crew":
        for image in page["images"]:
            if image["src"] == "legacy/ya.jpg":
                image["profile_key"] = "ya"
                image["profile_base"] = static(image["src"])
                image["profile_variants"] = [static(f"legacy/{name}.jpg") for name in ("yaup", "yacenter", "yadown")]
            elif image["src"] == "legacy/givi.jpg":
                image["profile_key"] = "givi"
                image["profile_base"] = static(image["src"])
                image["profile_variants"] = [static(f"legacy/{name}.jpg") for name in ("giviup", "givicenter", "gividown")]
        rotating_photos = [f"legacy/foto/old{number}sm.jpg" for number in OLD_CREW_ROTATION]
        rotation_added = False
        for image in page["images"]:
            if not rotation_added and image["src"] == "legacy/foto/old001sm.jpg":
                image["photo_cycle"] = [static(path) for path in rotating_photos]
                rotation_added = True
    page["article_groups"] = []
    for block in page["blocks"]:
        profile = block.get("profile")
        if profile and page["article_groups"] and page["article_groups"][-1]["profile"] == profile:
            page["article_groups"][-1]["blocks"].append(block)
        else:
            page["article_groups"].append({"profile": profile, "blocks": [block]})
    related_links = []
    for link in original.get("links", []):
        label = link.get("text") or link.get("title")
        target = link.get("target")
        if not label:
            continue
        if key == "track" and target in PAGE_URLS:
            continue
        if target in PAGE_URLS and target not in CORE_PAGES and target != key:
            href = reverse(PAGE_URLS[target])
        elif target and target.startswith("legacy/"):
            href = static(target)
        else:
            continue
        identity = (href, label)
        if identity not in {(item["href"], item["label"]) for item in related_links}:
            related_links.append({"href": href, "label": label, "title": link.get("title", "")})
    page["related_links"] = related_links
    if key == "home":
        history = legacy_pages().get("history", {})
        page["hero_image"] = next(iter(history.get("images", [])), None)
    if key == "track":
        enriched_routes = []
        for cells in page.get("routes", [])[1:]:
            year = cells[0].strip() if cells else ""
            image_path = cells[4] if len(cells) > 4 else ""
            image = next((item for item in page["images"] if image_path and item["src"] == image_path), None)
            photo_candidates = []
            if year in {"2006", "2007", "2009", "2010"}:
                seen_photos = set()
                for item in legacy_pages().get(year, {}).get("images", []):
                    if item.get("src") and item["src"] not in seen_photos:
                        photo_candidates.append(item["src"])
                        seen_photos.add(item["src"])
            enriched_routes.append({
                "year": year,
                "note": cells[1] if len(cells) > 1 else "",
                "route": cells[2] if len(cells) > 2 else "",
                "captain": cells[3] if len(cells) > 3 else "",
                "url": reverse(PAGE_URLS[year]) if year in PAGE_URLS else "",
                "image": image,
                "photo_candidates": photo_candidates,
            })
        page["route_rows"] = enriched_routes
        archive_images = []
        seen_full_images = set()
        for source_page in legacy_pages().values():
            for image in source_page.get("images", []):
                full = image.get("full") or image.get("src")
                if not full or full in seen_full_images:
                    continue
                seen_full_images.add(full)
                archive_images.append({
                    "src": image.get("src") or full,
                    "full": full,
                    "caption": image.get("caption", ""),
                    "source_title": source_page.get("title", ""),
                })
        page["archive_images"] = archive_images
    page["source_note"] = key in {"project", "history"}
    return render(request, "pages/legacy_page.html", {
        "page": page,
        "is_home": key == "home",
        "is_track": key == "track",
        "is_voyage": key in {"2006", "2007", "2009", "2010"},
        "is_coordinates": key == "coordinates",
    })


def home(request):
    return legacy_page(request, "home")


def project(request):
    return legacy_page(request, "project")


def history(request):
    return legacy_page(request, "history")


def crew(request):
    return legacy_page(request, "crew")


def voyages(request):
    return legacy_page(request, "track")


def coordinates(request):
    return legacy_page(request, "coordinates")


def oldspice(request):
    return legacy_page(request, "oldspice")


def voyage_2006(request):
    return legacy_page(request, "2006")


def voyage_2007(request):
    return legacy_page(request, "2007")


def voyage_2009(request):
    return legacy_page(request, "2009")


def voyage_2010(request):
    return legacy_page(request, "2010")


def registration(request):
    return render(request, "pages/registration.html")


def photo_archive(request):
    return HttpResponseRedirect(f"{reverse('voyages')}#photo-archive")


@staff_member_required(login_url=reverse_lazy("admin-login"))
def admin_dashboard(request):
    return render(request, "pages/admin_dashboard.html")


class AdminLoginView(LoginView):
    template_name = "pages/admin_login.html"
    redirect_authenticated_user = True


class AdminLogoutView(LogoutView):
    next_page = reverse_lazy("home")
