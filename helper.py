import bs4
import requests as rt
import tqdm

def check_keywords_presence(input_string):
    keywords = ["Gold", "Euro", "USD", "Oil"]
    found_keywords = []

    for keyword in keywords:
        if keyword.lower() in input_string.lower():
            found_keywords.append(keyword)

    return found_keywords

def scraper_for_keto_news():
    url = 'https://www.kitco.com/news/kitco-latest-news/'
    headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
    ses=rt.Session()
    content = ses.get(url,headers=headers)
    data=bs4.BeautifulSoup(content.text,'html.parser')
    temp = data.find('div',{'id':'left_column'})
    links = []
    for i in temp.find_all('a'):
        links.append('https://www.kitco.com' + i.attrs['href'])
    links = sorted(list(set(links)))
    article_data = {}
    for link in tqdm.tqdm(links,desc="Keto News Links"):
        try:
            headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
            #ses=rt.Session()
            content = ses.get(link,headers=headers)
            data=bs4.BeautifulSoup(content.text,'html.parser')
            temp = data.find('div',{'id':"article-info-title"})
            title = temp.find('h1', itemprop='name').text
            publish_date_time = data.find('span',{'class':"date"}).text
            try:
                temp2 = data.find('article', {'itemprop': 'articleBody'})
                paragraphs = []
                for paragraph in temp2.find_all('p'):
                    paragraphs.append(paragraph.text)
                article_text = ' '.join(paragraphs)
                article_text = article_text.replace('\n', '').replace('\r', '').replace('\t', '').strip()
            except Exception as e:
                #print(e)
                #print('Invalid Link: ',link)
                temp2 = data.find('div', {'itemprop': 'articleBody'})
                paragraphs = []
                for paragraph in temp2.find_all('p'):
                    paragraphs.append(paragraph.text)
                article_text = ' '.join(paragraphs[1:])
                article_text = article_text.replace('\n', '').replace('\r', '').replace('\t', '').strip()
            keywords_present = check_keywords_presence(title)
            keywords_present.extend(check_keywords_presence(article_text))
            keywords_present = list(set(keywords_present))
            if len(keywords_present) >= 1:
                article_data[link] = {}
                article_data[link]['Title'] = title
                article_data[link]['Date & Time'] = publish_date_time
                article_data[link]['Article Text'] = article_text
                article_data[link]['Keywords Present in Article Text'] = keywords_present
        except Exception as e:
            #print(e)
            #print('Invalid Link: ',link)
            continue
    return article_data

def extract_articles(response_json):
    articles = response_json.get("result", {}).get("articles", [])
    extracted_articles = []

    for article in articles:
        title = article.get("title")
        description = article.get("description")
        published_time = article.get("published_time")
        canonical_url = "https://www.reuters.com" + article.get("canonical_url")

        extracted_articles.append({
            "title": title,
            "description": description,
            "published_time": published_time,
            "canonical_url": canonical_url
        })

    return extracted_articles
def get_top100_articles_links():
    url = 'https://www.reuters.com/markets/commodities/'
    headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
    ses=rt.Session()
    content = ses.get(url,headers=headers)
    #data=bs4.BeautifulSoup(content.text,'html.parser')
    url = "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-section-alias-or-id-v1?query=%7B%22called_from_a_component%22%3Atrue%2C%22fetch_type%22%3A%22section%22%2C%22offset%22%3A0%2C%22orderby%22%3A%22last_updated_date%3Adesc%22%2C%22section_id%22%3A%22%2Fmarkets%2Fcommodities%22%2C%22size%22%3A100%2C%22website%22%3A%22reuters%22%7D&d=151&_website=reuters"

    # Make requests until all articles are fetched
    all_articles = []
    offset = 0
    size = 8
    total_size = 5  # Update this with the actual total_size value from the response

    while offset < total_size:
        # Update the offset parameter in the URL
        url_with_offset = url.replace("offset%3A0", f"offset%3A{offset}")

        # Make the GET request
        response = ses.get(url_with_offset)
        response_json = response.json()

        # Extract the articles from the current response
        articles = extract_articles(response_json)
        all_articles.extend(articles)

        # Increment the offset for the next request
        offset += size
    return all_articles

def scraper_for_reuters():
    url = 'https://www.reuters.com/markets/commodities/'
    headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
    ses=rt.Session()
    content = ses.get(url,headers=headers)
    data=bs4.BeautifulSoup(content.text,'html.parser')
    links = get_top100_articles_links()
    
    article_data = {}
    for link_data in tqdm.tqdm(links,desc="Reuters Links"):
        try:
            title = link_data['title']
            url = link_data['canonical_url']
            headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
            ses=rt.Session()
            content = ses.get(url,headers=headers)
            data=bs4.BeautifulSoup(content.text,'html.parser')
            temp = data.find_all('span',{'class':"date-line__date__23Ge-"})
            article_time = temp[1].text
            article_date = temp[0].text
            temp2 = data.find('div', {'class': 'article-body__container__3ypuX over-6-para'})
            paragraphs = []
            for paragraph in temp2.find_all('p'):
                paragraphs.append(paragraph.text)
            article_text = ' '.join(paragraphs[1:])
            keywords_present = check_keywords_presence(title)
            keywords_present.extend(check_keywords_presence(article_text))
    
        except Exception as e:
            #print(e)
            continue
        keywords_present = list(set(keywords_present))
        if len(keywords_present) >= 1:
            article_data[url] = {}
            article_data[url]['Title'] = title
            article_data[url]['Date & Time'] = article_date+ " " +article_time
            article_data[url]['Article Text'] = article_text
            article_data[url]['Keywords Present in Article Text'] = keywords_present
    return article_data

