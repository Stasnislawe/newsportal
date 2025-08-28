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
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType


class SimpleTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        firefox_options = Options()
        firefox_options.headless = True
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

        self.authors_group, created = Group.objects.get_or_create(name='authors')

        if created:
            # Добавляем права на добавление постов
            content_type = ContentType.objects.get_for_model(Post)
            add_permission = Permission.objects.get(
                content_type=content_type,
                codename='add_post'
            )
            self.authors_group.permissions.add(add_permission)
        else:
            print(f'Группа авторов не создана')

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
                print('Не найдено поле "Стать автором"')

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
                like_link_selector = 'a[href*="like"]:first-child'

                like_link = None
                try:
                    like_link = self.browser.find_element(By.CSS_SELECTOR, like_link_selector)
                except:
                    print('Не удалось найти ссылку лайка')

                if like_link:
                    # Получаем текущее количество лайков из БД
                    from ..models import Likes
                    initial_likes_count = Likes.objects.filter(rating=self.news).count()
                    # Изначально должно быть 0 лайков в БД

                    # Кликаем на ссылку лайка
                    like_link.click()
                    time.sleep(1)

                    # Проверяем изменение в БД после клика, должно стать 1 лайк в БД
                    final_likes_count = Likes.objects.filter(rating=self.news).count()

                    # Проверяем, что лайк увеличился на 1
                    self.assertEqual(final_likes_count, initial_likes_count + 1,
                                     f"Количество лайков должно увеличиться с {initial_likes_count} до {initial_likes_count + 1}, но стало {final_likes_count}")

                else:
                    print("Ссылка лайка не найдена")
                    self.browser.save_screenshot('like_link_not_found.png')

            except Exception as e:
                print(f"Ошибка при попытке поставить лайк: {e}")
                self.browser.save_screenshot('like_error.png')

            # Отправка сообщения пользователям
            try:
                users_url = f'{self.live_server_url}/chat/users/'
                self.browser.get(users_url)
                time.sleep(2)

                # Ищем кнопку "Написать сообщение пользователю ..."
                write_message_selector = 'a[href*="/chat/dialogs/create/"]'

                write_message_btn = None
                try:
                    write_message_btn = self.browser.find_element(By.CSS_SELECTOR, write_message_selector)
                except:
                    print(f'Не удалось найти кнопку')

                if write_message_btn:
                    write_message_btn.click()
                    time.sleep(1)

                    message_form_selector = 'form[method="post"]'

                    message_form = None
                    try:
                        message_form = self.browser.find_element(By.CSS_SELECTOR, message_form_selector)
                    except:
                        print(f'Не удалось найти форму сообщения')

                    if message_form:
                        message_input_selector = 'textarea[name="message"]'

                        message_input = None
                        try:
                            message_input = self.browser.find_element(By.CSS_SELECTOR, message_input_selector)
                        except:
                            print(f'Не удалось найти поле ввода сообщения')

                        if message_input:
                            # Вводим тестовое сообщение
                            test_message = "привет"
                            message_input.clear()
                            message_input.send_keys(test_message)

                            # Ищем кнопку отправки
                            send_button_selector = 'button[type="submit"]'

                            send_button = None
                            try:
                                send_button = self.browser.find_element(By.CSS_SELECTOR, send_button_selector)
                            except:
                                print(f'Не удалось найти кнопку отправки')

                            if send_button:
                                # Сохраняем текущее количество сообщений
                                from chat.models import Message
                                initial_message_count = Message.objects.count()

                                # Отправляем сообщение
                                send_button.click()
                                time.sleep(2)

                                # Проверяем, что сообщение сохранилось в БД
                                final_message_count = Message.objects.count()

                                # Проверяем увеличение количества сообщений
                                self.assertEqual(final_message_count, initial_message_count + 1,
                                                 "Количество сообщений должно увеличиться на 1")

                                # Ищем отправленное сообщение
                                try:
                                    sent_message = Message.objects.filter(message=test_message).latest('id')

                                    # Проверяем содержание сообщения
                                    self.assertEqual(sent_message.message, test_message,
                                                     "Текст сообщения должен совпадать с отправленным")

                                except Message.DoesNotExist:
                                    # Выводим все сообщения для отладки
                                    all_messages = Message.objects.all()
                                    print(f"Все сообщения в БД: {list(all_messages)}")
                                    raise Exception(f"Сообщение с текстом '{test_message}' не найдено в БД")

                            else:
                                print("Кнопка отправки не найдена")
                                self.browser.save_screenshot('send_button_not_found.png')

                        else:
                            print("Поле ввода сообщения не найдено")
                            self.browser.save_screenshot('message_input_not_found.png')

                    else:
                        print("Форма сообщения не найдена")
                        self.browser.save_screenshot('message_form_not_found.png')

                else:
                    print("Кнопка 'Написать сообщение пользователю' не найдена")
                    # Делаем скриншот для отладки
                    self.browser.save_screenshot('write_message_btn_not_found.png')
                    # Выводим HTML для отладки
                    print("HTML страницы:")
                    print(self.browser.page_source[:1000])

            except Exception as e:
                print(f"Ошибка при выполнении теста: {e}")
                self.browser.save_screenshot('debug_screenshot.png')
                print("Скриншот сохранен как debug_screenshot.png")
                raise

            try:
                # Добавляем пост через форму
                # Ищем кнопку "Добавить пост"
                add_post_selector = 'a[href*="/post/create/"]'

                add_post_btn = None
                try:
                    add_post_btn = self.browser.find_element(By.CSS_SELECTOR, add_post_selector)
                except:
                    print(f'Не удалось найти кнопку "Добавить пост"')

                if add_post_btn:
                    add_post_btn.click()
                    time.sleep(1)

                    # Заполняем форму создания поста
                    post_data = {
                        'heading': 'Тестовый пост из Selenium',
                        'text': 'Это тестовое содержание поста до изображения',
                        'text2': 'Это тестовое содержание поста после изображения',
                    }

                    # Заполняем поле "Наименование"
                    heading_selector = '[name="heading"]'
                    try:
                        heading_field = self.browser.find_element(By.CSS_SELECTOR, heading_selector)
                        heading_field.clear()
                        heading_field.send_keys(post_data['heading'])
                    except:
                        print(f'Не удалось найти поле "Наименование"')

                    # Заполняем поле "Содержание до изображения"
                    text_selector = '[name="text"]'
                    try:
                        text_field = self.browser.find_element(By.CSS_SELECTOR, text_selector)
                        text_field.clear()
                        text_field.send_keys(post_data['text'])
                    except:
                        print(f'Не удалось найти поле "Содержание до изображения"')

                    # Заполняем поле "Содержание после изображения"
                    text2_selector = '[name="text2"]'
                    try:
                        text2_field = self.browser.find_element(By.CSS_SELECTOR, text2_selector)
                        text2_field.clear()
                        text2_field.send_keys(post_data['text2'])
                    except:
                        print(f'Не удалось найти поле "Содержание после изображения"')

                    # Выбираем категорию (если есть)
                    category_selector = '[name="posts_mtm"]'
                    try:
                        category_field = self.browser.find_element(By.CSS_SELECTOR, category_selector)
                        from selenium.webdriver.support.ui import Select
                        select = Select(category_field)

                        # Пытаемся выбрать категорию по видимому тексту
                        try:
                            select.select_by_visible_text('Тестовая категория')
                        except:
                            # Если не получается по тексту, выбираем по value
                            options = select.options
                            for i, option in enumerate(options):
                                if 'Тестовая' in option.text:
                                    select.select_by_index(i)
                                    print(f"Выбрана категория по индексу {i}: {option.text}")
                                    break
                            else:
                                # Если ничего не найдено, выбираем первую доступную
                                select.select_by_index(0)
                                print("Выбрана первая доступная категория")

                    except Exception as e:
                        print(f"Ошибка при выборе категории: {e}")
                        pass

                    # Выбираем тип поста
                    post_type_selector = '[name="post_type"]'
                    try:
                        post_type_field = self.browser.find_element(By.CSS_SELECTOR, post_type_selector)
                        select = Select(post_type_field)
                        select.select_by_index(1)  # Выбираем первый вариант
                    except:
                        print(f'Не удалось найти поле "тип поста"')

                    # Загружаем изображение
                    image_selector = '[name="image"]'
                    try:
                        image_field = self.browser.find_element(By.CSS_SELECTOR, image_selector)
                        base_dir = settings.BASE_DIR
                        test_image_path = os.path.join(base_dir, 'media', 'nophoto.jpg')
                        if os.path.exists(test_image_path):
                            image_field.send_keys(test_image_path)
                    except:
                        print(f'Не удалось найти поле изображение')

                    # Сохраняем текущее количество постов в БД
                    initial_post_count = Post.objects.count()
                    # Текущее значение постов должно быть равно одному (1)

                    # Находим и нажимаем кнопку сохранения
                    submit_selector = 'input[type="submit"]'

                    submit_btn = None
                    try:
                        submit_btn = self.browser.find_element(By.CSS_SELECTOR, submit_selector)
                        if submit_btn:
                            submit_btn.click()
                    except:
                        print(f'Не удалось найти кнопку сохранения')

                    time.sleep(3)

                    # Проверяем, что пост сохранился в БД
                    final_post_count = Post.objects.count()

                    # Проверяем увеличение количества постов
                    self.assertEqual(final_post_count, initial_post_count + 1,
                                     "Количество постов должно увеличиться на 1")

                    # Ищем созданный пост
                    try:
                        created_post = Post.objects.filter(heading=post_data['heading']).latest('id')

                        # Проверяем содержание поста
                        self.assertEqual(created_post.heading, post_data['heading'])
                        self.assertEqual(created_post.text, post_data['text'])
                        self.assertEqual(created_post.text2, post_data['text2'])

                    except Post.DoesNotExist:
                        all_posts = Post.objects.all()
                        print(f"Все посты в БД: {list(all_posts)}")
                        raise Exception(f"Пост с заголовком '{post_data['heading']}' не найден в БД")

                else:
                    print("Кнопка 'Добавить пост' не найдена")
                    self.browser.save_screenshot('add_post_btn_not_found.png')

            except Exception as e:
                print(f"Ошибка при выполнении теста: {e}")
                self.browser.save_screenshot('debug_screenshot_.png')
                print("Скриншот сохранен как debug_screenshot.png")
                raise

        except Exception as e:
            print(f"Ошибка при выполнении теста: {e}")
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