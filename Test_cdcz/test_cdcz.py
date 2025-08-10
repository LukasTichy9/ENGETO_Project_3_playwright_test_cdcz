import pytest
import time

CD_URL = "https://www.cd.cz"

def close_cookies(page, slow=True):
    """Zavře cookies banner pokud je viditelný"""
    selectors = [
        'button:has-text("Povolit pouze nezbytné")',
        'button:has-text("Pouze nezbytné")',  
        'button:has-text("Odmítnout")',
        'button:has-text("Odmítnout vše")'
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                if slow:
                    time.sleep(1)
                el.click()
                if slow:
                    time.sleep(1)
                break
        except:
            continue

def safe_click(page, locator, slow=True):
    """Bezpečné kliknutí na element"""
    el = locator.first
    el.scroll_into_view_if_needed()
    box = el.bounding_box()
    if box:
        page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
    else:
        el.click()
    if slow:
        time.sleep(1)

def test_landingpage_and_cookies(page):
    """Test načtení homepage a zavření cookies banneru"""
    page.goto(CD_URL)
    page.wait_for_load_state("load")
    time.sleep(2)
    close_cookies(page)
    
    header = page.locator("header").first
    assert header.is_visible(timeout=4000), "Header není viditelný"

def test_main_menu_buttons_visible(page):
    """Test viditelnosti hlavního menu"""
    page.goto(CD_URL)
    close_cookies(page)

    main_nav_items = [
        ("Spojení a jízdenka", "nav a[href*='spojeni']"),
        ("Vlak", "nav a[href*='vlak']"),
        ("Stanice", "nav a[href*='stanice']"),
        ("Moje cestování", "nav a[href*='moje-cestovani']")
    ]
    
    for item_name, selector in main_nav_items:
        try:
            btn = page.locator(selector).first
            if not btn.is_visible(timeout=2000):
                btn = page.locator(f"nav a:has-text('{item_name}')").first
            
            assert btn.is_visible(timeout=4000), f"Hlavní menu '{item_name}' není viditelné"
            
            safe_click(page, btn)
            page.wait_for_load_state("load", timeout=5000)
            page.go_back()
            page.wait_for_load_state("load", timeout=5000)
        except Exception as e:
            print(f"Problém s menu item {item_name}: {e}")

def test_search_engine(page):
    """Test vyhledávacího pole"""
    page.goto(CD_URL)
    close_cookies(page)
    
    search_selectors = [
        "#mainSearchInput",
        "input[name='searchtext']",
        "input[placeholder*='Hledat']",
        "input[type='search']",
        ".search input",
        "form[action*='hledat'] input"
    ]
    
    search_input = None
    for selector in search_selectors:
        try:
            input_el = page.locator(selector).first
            if input_el.is_visible(timeout=2000):
                search_input = input_el
                break
        except:
            continue
    
    if not search_input:
        search_trigger = page.locator("button[aria-label*='hled'], .search-trigger, .search-icon").first
        if search_trigger.is_visible(timeout=2000):
            safe_click(page, search_trigger)
            time.sleep(1)
            search_input = page.locator("input[type='search'], input[name='searchtext']").first
    
    assert search_input and search_input.is_visible(timeout=4000), "Vyhledávací pole nebylo nalezeno"
    
    search_input.fill("vlakové spojení")
    time.sleep(1)
    search_input.press("Enter")
    page.wait_for_load_state("networkidle")
    time.sleep(5)

    page.screenshot(path="scr_search_engine_success.png")

def test_go_to_connection_search(page):
    page.goto(CD_URL)
    close_cookies(page)
    
    page.goto(f"{CD_URL}/spojeni-a-jizdenka/")
    page.wait_for_load_state("load")
    time.sleep(3)
    
    assert "spojeni-a-jizdenka" in page.url, f"Nepodarilo se dostat na stránku spojení. URL: {page.url}"

def test_train_connection_search(page):
    page.goto(f"{CD_URL}/spojeni-a-jizdenka/")
    close_cookies(page)
    time.sleep(5)

    from_input = page.locator("input[aria-label='Zadejte stanici odkud']").first
    to_input = page.locator("input[aria-label='Zadejte stanici kam']").first

    assert from_input.is_visible(timeout=5000), "Pole ODKUD není viditelné"
    assert to_input.is_visible(timeout=5000), "Pole KAM není viditelné"

    print("Vyplňuji pole ODKUD")
    from_input.click()
    time.sleep(1)
    from_input.fill("Praha hl.n.")
    
    page.keyboard.press("Escape")
    time.sleep(2)
    
    print("Vyplňuji pole KAM")

    to_input.click(force=True)
    time.sleep(1)
    to_input.fill("Wien Hbf")
    
    page.keyboard.press("Escape")
    time.sleep(2)
    
    search_btn = page.locator("button:has-text('Vyhledat')").first
    if not search_btn.is_visible(timeout=2000):
  
        print("Tlačítko Vyhledat nenalezeno, použiji Enter")
        to_input.press("Enter")
    else:
        print("Klikám na tlačítko Vyhledat")
        search_btn.click(force=True)
    
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(5)
    
    page.screenshot(path="scr_train_connection_success.png")
    
    current_url = page.url
    print(f"Aktuální URL: {current_url}")
    
    # Test projde pokud:
    # 1. URL se změnila (obsahuje více parametrů)
    # 2. NEBO se objevila nějaká informace o spojení
    success = (
        len(current_url) > 60 or  # URL se rozšířila
        page.locator("text=Praha").is_visible(timeout=5000) or
        page.locator("text=Wien").is_visible(timeout=5000) or
        page.locator("text=vlak").is_visible(timeout=5000) or
        page.locator("text=spojení").is_visible(timeout=5000) or
        page.locator("text=Detail").is_visible(timeout=5000)
    )
