from app.services.intent import classify_intent

def test_classify_scholarly_search():
    res = classify_intent("attention is all you need paper")
    assert res["intent"] == "scholarly_search"
    assert res["vertical"] == "research"
    assert res["requires_crawling"] is True

    res_doi = classify_intent("lookup DOI 10.1038/nphys1170")
    assert res_doi["intent"] == "scholarly_search"
    assert res_doi["vertical"] == "research"

def test_classify_news_monitoring():
    res = classify_intent("latest tech headlines about OpenAI")
    assert res["intent"] == "news_monitoring"
    assert res["vertical"] == "news"
    assert res["requires_freshness"] is True

def test_classify_entity_lookup():
    res = classify_intent("who is Alan Turing")
    assert res["intent"] == "entity_lookup"
    assert res["vertical"] == "entity"
    assert "Alan Turing" in res["entities"]

    res_noun = classify_intent("Google Inc")
    assert res_noun["intent"] == "entity_lookup"
    assert "Google Inc" in res_noun["entities"]

def test_classify_general_search():
    res = classify_intent("how do search engines index web pages")
    assert res["intent"] == "search_query"
    assert res["vertical"] == "web"
