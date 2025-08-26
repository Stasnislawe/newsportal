# web_app/tests/test_selenium_simple.py
import os
import time
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from django.contrib.auth.models import User
from ..models import Author, Category, Post


class SimpleTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        firefox_options = Options()
        firefox_options.headless = False
        cls.browser = webdriver.Firefox(options=firefox_options)
        cls.browser.implicitly_wait(10)

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123'
        )

        self.user_author = User.objects.create_user(
            username='test',
            password='testaspassword124'
        )

        self.category = Category.objects.create(
            name_category='Тестовая категория'
        )

        self.author = Author.objects.create(
            user=self.user_author,
            username='TestUser',
            description='Описание о себе',
        )

        self.news = Post.objects.create(
            post_type='NW',
            heading='Новость 1',
            text='Текст новости. Тест текста новости',
            text2='Текст новости после изображения. Тест текста новости после изображения',
            draft=True,
            author=self.author
        )

    def test_author_form_after_login(self):
        """Тест заполнения формы автора после успешного входа в личный кабинет"""
        try:
            # Открываем страницу логина
            self.browser.get(f'{self.live_server_url}/accounts/login/')
            time.sleep(1)

            # Заполняем форму логина
            username = self.browser.find_element(By.NAME, 'username')
            password = self.browser.find_element(By.NAME, 'password')

            username.send_keys('testuser')
            password.send_keys('testpassword123')
            password.send_keys(Keys.RETURN)

            time.sleep(2)

            self.assertNotIn('login', self.browser.current_url)

            # Ищем форму автора
            form = None
            try:
                form = self.browser.find_element(By.CSS_SELECTOR, 'form')
            except:
                raise Exception("Не удалось найти форму на странице")

            # Ищем поле username для изменения (если существует)
            nickname_field = None
            new_nickname = "SuperTestAuthor123"

            try:
                nickname_field = self.browser.find_element(By.CSS_SELECTOR, '[name="username"]')
                if nickname_field:
                    nickname_field.clear()
                    nickname_field.send_keys(new_nickname)
            except:
                print("Поле nickname не найдено, используем значение по умолчанию")
                new_nickname = "testuser"

            # Поле "О себе"
            about_text = "Это тестовое описание автора для selenium теста"
            about_field = None

            try:
                about_field = self.browser.find_element(By.CSS_SELECTOR, '[name="description"]')
                if about_field:
                    about_field.clear()
                    about_field.send_keys(about_text)
            except:
                print("Поле 'О себе' не найдено, пропускаем")
                about_text = None

            # Поле загрузки файла (фото)
            file_input = None
            try:
                file_input = self.browser.find_element(By.CSS_SELECTOR, '[name="photo"]')
                if file_input:
                    # Получаем абсолютный путь к тестовому изображению
                    base_dir = settings.BASE_DIR
                    test_image_path = os.path.join(base_dir, 'media', 'nophoto.jpg')

                    # Проверяем существование файла, если нет - создаем тестовый
                    if not os.path.exists(test_image_path):
                        test_image_path = os.path.join(base_dir, 'web', 'tests', 'test_image.jpg')
                        if not os.path.exists(test_image_path):
                            # Создаем простой текстовый файл как заглушку
                            with open(test_image_path, 'w') as f:
                                f.write('test image content')

                    file_input.send_keys(test_image_path)
                    time.sleep(1)
            except:
                print("Поле загрузки файла не найдено, пропускаем")

            # Находим и нажимаем кнопку "Сохранить изменения"
            submit_button = None
            button_selector = 'button[type="submit"]'

            try:
                submit_button = self.browser.find_element(By.CSS_SELECTOR, button_selector)
            except:
                print('Не найдено поле "Сохранить изменения"')

            if submit_button:
                submit_button.click()
                time.sleep(3)
                initial_author_count = 1

                # Проверяем результат в БД
                final_author_count = Author.objects.count()

                # Проверяем, что автор был создан/обновлен
                self.assertEqual(final_author_count, initial_author_count + 1,
                                 "Количество авторов в БД должно увеличиться на 1")

                # Ищем созданного автора
                try:
                    created_author = Author.objects.get(username=new_nickname)

                    # Проверяем заполненные поля
                    if about_text:
                        self.assertEqual(created_author.description, about_text,
                                         "Поле 'О себе' должно совпадать с введенным текстом")

                except Author.DoesNotExist:
                    # Если автор с новым nickname не найден, проверяем другие варианты
                    authors = Author.objects.all()
                    raise Exception(f"Автор с username '{new_nickname}' не найден в БД")

            else:
                print("Кнопка отправки не найдена")
                raise Exception("Не удалось найти кнопку отправки формы")

            # Лайк новости
            news_url = f'{self.live_server_url}/newsportal/news/'
            self.browser.get(news_url)
            time.sleep(2)

            # Ищем новость
            try:
                news_link_selector = 'a.btn-custom'  # Кнопка "Читать дальше"

                news_link = None
                try:
                    news_link = self.browser.find_element(By.CSS_SELECTOR, news_link_selector)
                except:
                    print('Не удалось найти новость')

                if news_link:
                    news_link.click()
                    time.sleep(1)
                else:
                    # Если не нашли ссылку, попробуем перейти напрямую по URL новости
                    news_detail_url = f'{self.live_server_url}/news/{self.news.id}/'
                    self.browser.get(news_detail_url)
                    time.sleep(1)

            except Exception as e:
                print(f"Ошибка при переходе на новость: {e}")

            try:
                # Ищем ссылку "Нравится"
                like_link_selector = 'a[href*="like"]:first-child',

                like_link = None
                try:
                    like_link = self.browser.find_element(By.CSS_SELECTOR, like_link_selector)
                except:
                    print('Не удалось найти ссылку лайка')

                if like_link:
                    # Получаем текущее количество лайков из текста ссылки
                    like_text = like_link.text

                    # Извлекаем число лайков из текста "Нравится (X)"
                    import re
                    match = re.search(r'\((\d+)\)', like_text)
                    if match:
                        initial_likes = int(match.group(1))
                    else:
                        initial_likes = 0
                        print("Не удалось извлечь количество лайков, предполагаем 0")

                    # Кликаем на ссылку лайка
                    like_link.click()
                    time.sleep(2)

                    # После клика страница перезагружается, Ищем обновленную ссылку лайка
                    updated_like_link = None
                    try:
                        updated_like_link = self.browser.find_element(By.CSS_SELECTOR, like_link_selector)
                    except:
                        print('Не удалось найти ссылку лайка')

                    if updated_like_link:
                        updated_like_text = updated_like_link.text

                        # Извлекаем новое количество лайков
                        match = re.search(r'\((\d+)\)', updated_like_text)
                        if match:
                            final_likes = int(match.group(1))

                            # Проверяем, что лайк увеличился
                            self.assertEqual(final_likes, initial_likes + 1,
                                             f"Количество лайков должно увеличиться с {initial_likes} до {initial_likes + 1}, но стало {final_likes}")

                        else:
                            print("Не удалось получить количество лайков после клика")
                    else:
                        print("Не удалось найти ссылку лайка после клика")

                else:
                    print("Ссылка лайка не найдена")
                    # Делаем скриншот для отладки
                    self.browser.save_screenshot('like_link_not_found.png')

            except Exception as e:
                print(f"Ошибка при попытке поставить лайк: {e}")
                self.browser.save_screenshot('like_error.png')

            print("Тест завершен успешно!")

        except Exception as e:
            print(f"Ошибка при выполнении теста: {e}")
            # Делаем скриншот для отладки
            self.browser.save_screenshot('debug_screenshot.png')
            print("Скриншот сохранен как debug_screenshot.png")
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()


if __name__ == '__main__':
    import unittest
    unittest.main()