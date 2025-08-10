"""
Automation script for submitting proposals on the Bahr freelance
platform.

This script demonstrates how you can automate the same actions
performed manually in the browser while assisting you.  It uses the
Selenium WebDriver library to drive a Chrome browser, navigate
through the site, log in with your credentials, find specific
projects, and submit proposals with the appropriate rates and
descriptions.

Please note that websites evolve over time and selectors may change.
You may need to adjust the CSS/XPath selectors in this script to
match the current structure of Bahr’s website.  Additionally, this
script leaves placeholders for your login credentials and the
proposal messages.  Fill those in before running it.

To use this script you need to install the following Python
packages:

  pip install selenium webdriver-manager

The webdriver‑manager package automatically downloads the correct
ChromeDriver for your version of Chrome.  If you are using a
different browser, adjust the imports accordingly.

Usage example:

    python bahr_automation.py

The script will open a Chrome window, log in to your account,
switch the interface to English, and sequentially submit proposals
for a predefined list of projects.  Modify the `PROJECTS_TO_APPLY`
list near the bottom of this file to match the projects and terms
you wish to apply for.

"""

from __future__ import annotations

import time
from dataclasses import dataclass

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class ProjectApplication:
    """Structure to hold information needed to apply to a project."""

    title: str
    project_type: str  # 'monthly' or 'per_project'
    rate: int  # Monthly rate or total rate for per project
    duration_days: int | None = None  # For per project projects
    milestones: list[tuple[str, int]] | None = None  # For per project projects
    brief: str = ""


def initialize_driver(headless: bool = False) -> webdriver.Chrome:
    """Initialize a Chrome WebDriver instance.

    Args:
        headless: Whether to run Chrome in headless mode. Default is
            False so you can watch the automation.  Set to True for
            background operation.

    Returns:
        A configured instance of selenium WebDriver.
    """
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    # Suppress logging for cleaner output
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.maximize_window()
    return driver


def login(driver: webdriver.Chrome, username: str, password: str, timeout: int = 30) -> None:
    """Log in to the Bahr platform using provided credentials.

    This function navigates to the login page, enters the user name and
    password, and submits the login form.  It waits for the dashboard
    to load before returning.  Update the CSS/XPath selectors as needed.

    Args:
        driver: Selenium WebDriver instance.
        username: Your Bahr username or email.
        password: Your Bahr password.
        timeout: Maximum time in seconds to wait for the login
            sequence to complete.
    """
    driver.get("https://bahr.sa/en/login")
    wait = WebDriverWait(driver, timeout)

    # Locate username/email input field and enter username
    try:
        username_field = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='email'], input[type='email']")
            )
        )
        username_field.clear()
        username_field.send_keys(username)
    except TimeoutException:
        raise RuntimeError("Could not find username field on login page.")

    # Locate password input field and enter password
    try:
        password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password']")
        password_field.clear()
        password_field.send_keys(password)
    except NoSuchElementException:
        raise RuntimeError("Could not find password field on login page.")

    # Submit the login form
    password_field.send_keys(Keys.RETURN)

    # Wait for dashboard or projects page to load (identified by presence of Projects menu)
    try:
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//nav//a[contains(@href, '/projects')]"))
        )
    except TimeoutException:
        raise RuntimeError("Login failed or dashboard did not load within the timeout.")


def switch_language_to_english(driver: webdriver.Chrome, timeout: int = 15) -> None:
    """Ensure the interface is set to English.

    Bahr defaults to Arabic for many users; there is a globe icon on the
    page that toggles the language.  This function checks if the
    language is already English by looking for English text on the
    Projects menu.  If not, it clicks the globe icon.
    """
    wait = WebDriverWait(driver, timeout)
    try:
        # Check if the Projects link is already in English
        projects_link = driver.find_element(By.XPATH, "//nav//a[contains(@href, '/projects')]")
        if 'Projects' in projects_link.text:
            return  # Already in English
    except NoSuchElementException:
        pass

    # Find and click the language toggle (globe icon)
    try:
        lang_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Change language'], .language-toggle"))
        )
        lang_button.click()
        # Allow time for page refresh to English
        time.sleep(2)
    except TimeoutException:
        print("Language toggle not found; continuing in default language.")


def navigate_to_projects(driver: webdriver.Chrome) -> None:
    """Navigate to the list of open projects.

    Assumes the user is already logged in and at the dashboard.  Clicks
    the Projects link in the top navigation bar and waits for the
    projects list to load.
    """
    wait = WebDriverWait(driver, 15)
    projects_link = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//nav//a[contains(@href, '/projects')]") )
    )
    projects_link.click()

    # Wait for project cards to load (they contain the project type as a tag)
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='project-card'], article[class*='project']"))
    )


def open_project(driver: webdriver.Chrome, title: str, timeout: int = 15) -> None:
    """Open a project from the list by its title.

    This function scrolls through the projects list until it finds the
    project card containing the given title and clicks it.  Adjust
    selectors based on the actual markup of Bahr’s projects page.
    """
    wait = WebDriverWait(driver, timeout)
    # Use a loop to scroll down until we find the project card
    while True:
        # Try to locate the project card by partial match of its title
        try:
            project_card = driver.find_element(By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{title.lower()}')]")
            project_card.click()
            break
        except NoSuchElementException:
            # Scroll down a bit and continue searching
            driver.execute_script("window.scrollBy(0, 400)")
            time.sleep(1)
        # Optionally add a condition to break if end of list is reached
    # Wait for project details page to load (presence of Submit proposal button)
    wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Submit proposal')]")))


def submit_monthly_proposal(driver: webdriver.Chrome, rate: int, brief: str, timeout: int = 20) -> None:
    """Fill in and submit a proposal for a monthly project.

    Assumes that the project details page is already open and the
    'Submit proposal' button is visible.  This function opens the
    proposal form, fills in the monthly rate and brief, checks the
    mandatory communication agreement checkbox, and submits the form.
    """
    wait = WebDriverWait(driver, timeout)
    # Click the Submit proposal button on project page
    submit_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Submit proposal')]"))
    )
    submit_btn.click()

    # Wait for rate input field
    rate_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='monthlyRate'], input[type='number']"))
    )
    rate_input.clear()
    rate_input.send_keys(str(rate))

    # Fill brief (text area)
    brief_field = driver.find_element(By.CSS_SELECTOR, "textarea[name='brief'], textarea")
    brief_field.clear()
    brief_field.send_keys(brief)

    # Check communication agreement checkbox
    try:
        agreement_checkbox = driver.find_element(By.XPATH, "//input[@type='checkbox']")
        if not agreement_checkbox.is_selected():
            agreement_checkbox.click()
    except NoSuchElementException:
        print("Agreement checkbox not found; skipping")

    # Submit the proposal
    submit_final_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit proposal') and @type='submit']")
    submit_final_btn.click()

    # Wait for confirmation page
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(., 'My proposal') or contains(., 'Pending')]"))
    )


def submit_per_project_proposal(
    driver: webdriver.Chrome,
    total_rate: int,
    duration_days: int,
    milestones: list[tuple[str, int]],
    brief: str,
    timeout: int = 30,
) -> None:
    """Fill in and submit a proposal for a per-project task.

    Per-project projects on Bahr require entering the project duration
    (in days), number of milestones, and details for each milestone
    (description and price).  This function opens the proposal form,
    fills in these fields, writes the brief, checks the agreement
    checkbox and submits.
    
    Args:
        driver: WebDriver instance.
        total_rate: The sum of all milestone prices; this value is not
            entered directly but should equal the sum of milestone amounts.
        duration_days: Estimated time to deliver the project in days.
        milestones: A list of tuples (description, price) representing
            each milestone.
        brief: The proposal text.
        timeout: Maximum wait time in seconds.
    """
    wait = WebDriverWait(driver, timeout)
    # Click Submit proposal button to open form
    submit_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Submit proposal')]"))
    )
    submit_btn.click()

    # Enter project duration
    duration_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='duration'], input[placeholder='Duration']"))
    )
    duration_input.clear()
    duration_input.send_keys(str(duration_days))

    # Enter number of milestones
    milestones_input = driver.find_element(By.CSS_SELECTOR, "input[name='milestones'], input[placeholder='Number of milestones']")
    milestones_input.clear()
    milestones_input.send_keys(str(len(milestones)))

    # For each milestone, add description and price
    for idx, (description, price) in enumerate(milestones, start=1):
        # Add milestone fields; there may be an 'Add milestone' button for the second and subsequent entries
        if idx > 1:
            add_milestone_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add milestone')]"))
            )
            add_milestone_btn.click()

        # Description fields often have name attributes like milestoneName-0
        desc_field = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"input[name^='milestoneName-']")
            )
        )
        # Because multiple inputs share the same pattern, we select all and pick the last for new milestone
        desc_fields = driver.find_elements(By.CSS_SELECTOR, "input[name^='milestoneName-']")
        price_fields = driver.find_elements(By.CSS_SELECTOR, "input[name^='milestonePrice-']")
        # Fill the latest elements
        desc_fields[-1].clear()
        desc_fields[-1].send_keys(description)
        price_fields[-1].clear()
        price_fields[-1].send_keys(str(price))

    # Write the brief
    brief_area = driver.find_element(By.CSS_SELECTOR, "textarea[name='brief'], textarea")
    brief_area.clear()
    brief_area.send_keys(brief)

    # Check communications agreement
    try:
        agreement_checkbox = driver.find_element(By.XPATH, "//input[@type='checkbox']")
        if not agreement_checkbox.is_selected():
            agreement_checkbox.click()
    except NoSuchElementException:
        print("Agreement checkbox not found; skipping")

    # Submit
    submit_final_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit proposal') and @type='submit']")
    submit_final_btn.click()
    # Wait for confirmation of submission
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(., 'My proposal') or contains(., 'Pending')]"))
    )


def apply_to_project(driver: webdriver.Chrome, project: ProjectApplication) -> None:
    """High-level function to open a project by title and submit a proposal.

    Determines whether the project is monthly or per-project and calls
    the appropriate helper function to submit the proposal.
    """
    print(f"Applying to project: {project.title}")
    open_project(driver, project.title)
    if project.project_type.lower() == 'monthly':
        submit_monthly_proposal(driver, rate=project.rate, brief=project.brief)
    elif project.project_type.lower() in {'per_project', 'per-project', 'per project'}:
        if project.duration_days is None or project.milestones is None:
            raise ValueError("Per-project applications require duration_days and milestones.")
        submit_per_project_proposal(
            driver,
            total_rate=project.rate,
            duration_days=project.duration_days,
            milestones=project.milestones,
            brief=project.brief,
        )
    else:
        raise ValueError(f"Unknown project type: {project.project_type}")


def main():
    # Replace with your actual Bahr credentials
    USERNAME = "your_username_or_email"
    PASSWORD = "your_password"

    # Define the projects you want to apply to.  The titles must match
    # the text on the Bahr platform.  Ensure that the rate, duration,
    # milestones and brief correspond to what you intend to submit.
    PROJECTS_TO_APPLY: list[ProjectApplication] = [
        ProjectApplication(
            title="Managing the association's official website",  # adjust if needed
            project_type='monthly',
            rate=1500,
            brief=(
                "مرحبًا، لدي خبرة في دعم وإدارة المواقع الرسمية. سأعمل على تحديث البيانات "
                "وتنفيذ سياسات الحوكمة وضمان عمل الموقع بسلاسة على مدار الساعة."
            ),
        ),
        ProjectApplication(
            title="Field marketer",  # adjust to match the Arabic title if necessary
            project_type='monthly',
            rate=1,
            brief=(
                "مرحبًا، أنا مسوق ميداني ذو خبرة ومهارات عالية في الإقناع والتواصل. أستطيع "
                "زيارة المواقع المستهدفة للتعريف بالمنتجات وإتمام التعاقدات."
            ),
        ),
        ProjectApplication(
            title="Freelancer in public relations & marketing",  # adjust accordingly
            project_type='monthly',
            rate=1500,
            brief=(
                "أهلاً، لدي خبرة واسعة في التسويق الرقمي والعلاقات العامة. يمكنني العمل عن بعد أو من "
                "مكتب الشركة في الرياض لزيادة الوعي وتنفيذ استراتيجيات تسويقية فعالة."
            ),
        ),
        ProjectApplication(
            title="Experience in integration between systems",  # adjust to full Arabic title
            project_type='monthly',
            rate=8000,
            brief=(
                "أتمتع بخبرة كبيرة كمهندس DevOps في تكامل الأنظمة وإدارة مسارات CI/CD وتشغيل الخوادم "
                "السحابية. سأقوم بتحليل المتطلبات وتصميم وتنفيذ حلول التكامل بفعالية."
            ),
        ),
        ProjectApplication(
            title="Writing content for Arabic/English website",  # adjust if necessary
            project_type='per_project',
            rate=3000,
            duration_days=20,
            milestones=[
                ("كتابة وتدقيق المحتوى العربي", 1500),
                ("كتابة وتدقيق المحتوى الإنجليزي والمراجعة النهائية", 1500),
            ],
            brief=(
                "أتمتع بخبرة طويلة في كتابة وتحرير المحتوى باللغتين العربية والإنجليزية. سأضمن نصوصًا "
                "متقنة ومراجعة شاملة ضمن المهلة الزمنية المحددة."
            ),
        ),
    ]

    driver = initialize_driver(headless=False)
    try:
        login(driver, USERNAME, PASSWORD)
        switch_language_to_english(driver)
        navigate_to_projects(driver)
        for project in PROJECTS_TO_APPLY:
            try:
                apply_to_project(driver, project)
                # Return to projects list after each application
                navigate_to_projects(driver)
            except Exception as e:
                print(f"Failed to apply to {project.title}: {e}")
                navigate_to_projects(driver)
        print("Finished applying to projects.")
    finally:
        # Optionally close the browser when done
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    main()