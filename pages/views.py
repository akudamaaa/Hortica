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
        if block.get("type") == "image":
            block["src"] = static(block["src"]) if block.get("src") else ""
            block["full"] = static(block["full"]) if block.get("full") else block["src"]
            if block.get("href"):
                block["resolved_href"] = source_link(original, {"href": block["href"]})
        for part in block.get("parts", []):
            if part.get("type") == "link":
                part["resolved_href"] = source_link(original, part)
    page["images"] = [
        {**image, "src_path": image["src"]}
        for image in original.get("images", [])
        if image.get("src")
    ]
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
        page["crew_old_cover"] = next(
            (image for image in page["images"] if image.get("caption") == "Фотографии тех лет"),
            None,
        )
        if page["crew_old_cover"]:
            page["crew_old_cover"]["photo_cycle"] = [static(path) for path in rotating_photos]
    page["article_groups"] = []
    for block in page["blocks"]:
        profile = block.get("profile")
        if profile and page["article_groups"] and page["article_groups"][-1]["profile"] == profile:
            page["article_groups"][-1]["blocks"].append(block)
        else:
            page["article_groups"].append({"profile": profile, "blocks": [block]})
    if key == "crew":
        blocks = page["blocks"]
        image_by_path = {image["src_path"]: image for image in page["images"]}

        def member(name_index, role_index, bio_indexes, *photo_paths):
            photos = []
            for path in photo_paths:
                image = image_by_path.get(path)
                if image:
                    photos.append(image)
            return {
                "name": blocks[name_index]["text"],
                "role": blocks[role_index]["text"],
                "bio": [blocks[index] for index in bio_indexes],
                "photos": photos,
                "profile_key": photos[0].get("profile_key", "") if photos else "",
            }

        page["crew_intro"] = blocks[1:6]
        page["crew_jump_links"] = blocks[6:9]
        page["crew_current_title"] = blocks[9]
        page["crew_current"] = [
            member(10, 11, [], "legacy/kaptan.jpg"),
            member(12, 13, [], "legacy/masha.jpg"),
            member(14, 15, [16, 17], "legacy/enot.jpg"),
            member(18, 19, [20], "legacy/ya.jpg"),
            member(21, 22, [23], "legacy/givi.jpg"),
            member(24, 25, [26], "legacy/olka.jpg"),
            member(27, 28, [29], "legacy/karas.jpg"),
            member(30, 31, [32], "legacy/kuzmich.jpg"),
        ]
        page["crew_back_current"] = blocks[33]
        page["crew_old_title"] = blocks[34]
        page["crew_old_intro"] = blocks[35:38]
        page["crew_old"] = [
            member(38, 39, [], "legacy/oldgavr.jpg"),
            member(40, 41, [], "legacy/olddilevich.jpg"),
            member(42, 43, [], "legacy/oldtarando.jpg"),
            member(44, 45, [], "legacy/oldvahm.jpg", "legacy/newvahm.jpg"),
            member(46, 47, [], "legacy/oldseva.jpg", "legacy/newseva.jpg"),
            member(48, 49, [], "legacy/oldvolk.jpg", "legacy/newvolk.jpg"),
            member(50, 51, [], "legacy/oldmamont.jpg", "legacy/newmamont.jpg"),
            member(52, 53, [], "legacy/oldlesha.jpg", "legacy/newlesha.jpg"),
            member(54, 55, [], "legacy/oldplu.jpg", "legacy/newplu.jpg"),
            member(56, 57, [], "legacy/oldrybkin.jpg", "legacy/newrybkin.jpg"),
            member(58, 59, [], "legacy/oldengelson.jpg", "legacy/newengelson.jpg"),
        ]
        page["crew_back_old"] = blocks[60]
        page["crew_young_title"] = blocks[61]
        page["crew_young_intro"] = blocks[62:64]
        page["crew_young"] = [
            member(64, 65, [], "legacy/kozer1.jpg"),
            member(66, 67, [], "legacy/kozer2.jpg"),
        ]
        page["crew_back_young"] = blocks[68]
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
