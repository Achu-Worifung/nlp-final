from ddgs import DDGS 

def google_search(query, max_results=10):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                'title': r.get('title'),
                'link': r.get('href'),
                'snippet': r.get('body')
            })
    return results

result = google_search("the lord is my shepherd", max_results=2)

for item in result:
    print(f"Title: {item['title']}")
    print(f"Link: {item['link']}")
    print(f"Snippet: {item['snippet']}\n")