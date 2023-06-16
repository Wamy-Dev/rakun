from jikanpy import Jikan
import hashlib
import urllib.parse
import requests
import time

jikan = Jikan()
'''
An end result should look like this:
{
    "id": "HASH",
    "title": "TITLE",
    "titles": ["EXTRA TITLES", "EXTRA TITLES"],
    "type": "TYPE",
    "mal_id": "MAL_ID",
    "ani_id": "ANI_ID",
    "link": {
        "source": "LINK",
        "source": "LINK"
    },
    "metadata": {
        "poster": "POSTERURL",
        "banner": "BANNERURL",
        "synopsis": "SYNOPSIS",
        "tags": ["TAGS", "TAGS"],
        "score": "SCORE",
        "rank": "RANK",
        "status": "STATUS",
        "episodes_num": "EPISODES",
        "aired": "AIRED",
        "studio": "STUDIO",
        "external_links": ["EXTERNAL_LINKS", "EXTERNAL_LINKS"],
        "episodes": [{
            "title": "TITLE",
            "number": "NUMBER",
            "aired": "AIRED",
        }],
        "trailer": "TRAILERURL",
        "images": ["IMAGES", "IMAGES"],
        "nyaarss": ["NYAARSS"],
    }
}
'''
def getAnilistID(mal_id, item_type):
    try:
        query = '''query($id: Int, $type: MediaType){Media(idMal: $id, type: $type){id}}'''
        variables = {
            "id": mal_id,
            "type": item_type.upper()
        }
        ani_id = requests.post("https://graphql.anilist.co", json={"query": query, "variables": variables}).json()["data"]["Media"]["id"]
        return ani_id
    except Exception as e:
        print(e)
        return None
def getStreamingLinks(data, links):
    streaming_links = []
    for previous_link in links:
        streaming_links.append(previous_link)
    if data:
        for link in data:
            source = link["name"]
            link = link["url"]
            streaming_links.append({source: link})
    return streaming_links
def getCharactersVoiceActors(mal_id, item_type):
    characters = []
    voice_actors = []
    if item_type == "Anime" or item_type == "EroAnime":
        characters_data = jikan.anime(mal_id, extension="characters")["data"]
        time.sleep(0.5)
        for character in characters_data:
            characters.append(character["character"]["name"])
            for voiceActor in character["voice_actors"]:
                voice_actors.append(voiceActor["person"]["name"])
    elif item_type == "Manga" or item_type == "EroManga":
        characters_data = jikan.manga(mal_id, extension="characters")["data"]
        for character in characters_data:
            characters.append(character["character"]["name"])

    return {
        "characters": characters,
        "voice_actors": voice_actors
    }
def getTitles(data):
    titles = []
    for title in data["titles"]:
        titles.append(title["title"])
    return titles
def getTags(data):
    tags = []
    for each in data["genres"]:
        tags.append(each["name"])
    for each in data["themes"]:
        tags.append(each["name"])
    for each in data["demographics"]:
        tags.append(each["name"])
    return tags
def getStudios(data):
    studios = []
    for each in data["studios"]:
        studios.append(each["name"])
    return studios
def getEpisodes(mal_id, item_type):
    episodes = []
    if item_type == "Anime" or item_type == "EroAnime":
        episodes_data = jikan.anime(mal_id, extension="episodes")["data"]
        time.sleep(0.5)
        number = 1
        for episode in episodes_data:
            episodes.append({
                "title": episode["title"],
                "aired": episode["aired"],
                "number": number
            })
            number += 1
        return episodes
    else:
        return []
def getJikanMetadata(mal_id, item_type, links):
    data = {}
    if item_type == "Anime" or item_type == "EroAnime":
        metadata = jikan.anime(mal_id, extension="full")
        time.sleep(0.5)
        # streaming links
        data["link"] = getStreamingLinks(metadata["data"]["streaming"], links)
    elif item_type == "Manga" or item_type == "EroManga":
        metadata = jikan.manga(mal_id, extension="full")
        time.sleep(0.5)
    title = metadata["data"]["title"]
    data["poster"] = metadata["data"]["images"]["webp"]["large_image_url"]
    data["banner"] = None
    data["synopsis"] = metadata["data"]["synopsis"]
    data["tags"] = getTags(metadata["data"])
    data["score"] = metadata["data"]["score"]
    data["rank"] = metadata["data"]["rank"]
    data["status"] = metadata["data"]["status"]
    data["episodes"] = getEpisodes(mal_id, item_type)
    data["aired"] = metadata["data"]["aired"]
    data["external_links"] = metadata["data"]["external"]
    data["episodes_num"] = metadata["data"]["episodes"]
    data["trailer"] = metadata["data"]["trailer"]["url"]
    data["images"] = []
    characters_voiceactors = getCharactersVoiceActors(mal_id, item_type)
    data["characters"] = characters_voiceactors["characters"]
    data["voice_actors"] = characters_voiceactors["voice_actors"]
    data["studios"] = getStudios(metadata["data"])
    data["nyaarss"] = f"https://sukebei.nyaa.si/?page=rss&q={urllib.parse.quote_plus(title)}&c=0_0&f=0" if item_type == "EroAnime" or item_type == "EroManga" else f"https://nyaa.si/?page=rss&q={urllib.parse.quote_plus(title)}&c=0_0&f=0"  # noqa: E501
    
    data["titles"] = getTitles(metadata["data"])
    data["content_type"] = metadata["data"]["type"]
    
    return data
def getMetadata(item):
    # get the keys of the item to access the data
    keys = list(item.keys())
    item_name, item_type = eval(keys[0])
    item = item[keys[0]]
    if item["mal_id"] is None:
        return {
            "id": hashlib.md5((item_name + item_type).encode()).hexdigest(),
            "title": item_name,
            "titles": [], 
            "type": item_type,
            "content_type": "TV" if item_type == "Anime" or item_type == "EroAnime" else "Manga",
            "mal_id": None,
            "ani_id": None,
            "link": item["link"],
            "metadata": {
                "poster": None,
                "banner": None,
                "synopsis": "This item does not have a synopsis.",
                "tags": [],
                "score": -1,
                "rank": -1,
                "status": "Finished Airing",
                "episodes": [],
                "aired": None,
                "external_links": [],
                "episodes_num": -1,
                "trailer": None,
                "images": [],
                "characters": [],
                "voice_actors": [],
                "studios": None,
                "nyaarss": f"https://sukebei.nyaa.si/?page=rss&q={urllib.parse.quote_plus(item_name)}&c=0_0&f=0" if item_type == "EroAnime" or item_type == "EroManga" else f"https://nyaa.si/?page=rss&q={urllib.parse.quote_plus(item_name)}&c=0_0&f=0"  # noqa: E501
            }
        }
    else:
        data = {}
        data["id"] = hashlib.md5((item_name + item_type).encode()).hexdigest()
        data["title"] = item_name
        data["mal_id"] = item["mal_id"]
        data["ani_id"] = getAnilistID(item["mal_id"], item_type)
        metadata = getJikanMetadata(item["mal_id"], item_type, item["link"])
        data["link"] = metadata["link"]
        data["titles"] = metadata["titles"]
        data["type"] = item_type
        data["content_type"] = metadata["content_type"]

        # remove link, content_type and titles from metadata
        metadata.pop("link")
        metadata.pop("content_type")
        metadata.pop("titles")
        data["metadata"] = metadata

        return data


