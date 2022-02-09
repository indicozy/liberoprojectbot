import feedparser
from bs4 import BeautifulSoup
NewsFeed = feedparser.parse("https://liberoproject.kz/feed/")
entry = NewsFeed.entries[0]

# ['title', 'title_detail', 'links', 'link', 'comments', 'authors', 'author', 'author_detail', 'published', 'published_parsed', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content', 'wfw_commentrss', 'slash_comments']
for i in NewsFeed.entries:
    soup = BeautifulSoup(i["summary"], 'html.parser')
    thumbnail = soup.find("img", {"class": "attachment-post-thumbnail"})["src"]
    images = [x["src"] for x in soup.find_all("img")]
    summary = []
    texts = soup.find_all("p")
    for j in texts:
        text = j.get_text().strip()
        if text:
            summary.append(text)
    summary = "\n".join(summary[:-1])
    total = {"link": i["link"],
            "title": i["title"],
            "author": i["author"],
            "published": i["published"],
            "published_parsed": i["published_parsed"],
            "tags": i["tags"],
            "thumbnail": thumbnail,
            "images": images,
            "summary": summary,
            }
    print(total["published_parsed"])
