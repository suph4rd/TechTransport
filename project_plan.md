
# Паша транспорт project (Tech transport):


### Вопросы 29.03.2026
    2. Что по справочнику
    3. Иерархия справочника (вид, категария и тд, на что будет подразделяться)
    4. 



### Этапы:
    1. Базовый бекенд, без payment service
    2. Базовый форонтенд, карта (VueJS)

[//]: # (    3. Внедрение Payment system)


### Техническое описание
    1. Фронт + бек (пока в 1м репозитории, потом разделим если что)
    2. Фронт
        1. VueJS
        2. Карта от OpenStreetMap
    3. Бекенд
        1. python, fastapi

[//]: # (    4. Где развернем тестовую зону?)


### Первоначальные мысли:
    1. На карте отображается техника и ее статус
    2. Бабки с подписки владелцев техники на карте
    3. Заказчики видят технику и номер водилы, сами звонят и утрясают детали
    4. Справочник техники (На лехе)
    5. Фотка именно этой техники (Скорее всего тоже на лехе)
    6. Авторизация по мобилка (как в доставке)
        1. Продумать все нюансы и возможные варики
        2. Только через мобила + смс вход?
    7. Персональные данные держателя техники (имя фамилия)
    8. Подробно описание самой техники
    9. Дизайн как в сами спецтехник (левый проект)
    10. Индикатор активности техники (активен/неактивен)
        1. Если не активен то не показываем на карте
    11. Какая карта?
        1. Любая бесплатная
        2. openStreetMap
            1. Лицензия - просто ссылка на их сайт
    12. Классификатор техники
        1. Номенклатура техники с видами
        2. Иконки техники
    13. Трекинг не через локацию а юзер сам ставит пин куда надо



# Model list:

## User:
    1. phone - main field, unique only if is_active
    2. is_active - in general, can we see user or not
    3. is_working - current technic status (Active/Inactive) true/false 
    4. username - just for identify (fio and something else)


## Transport:
    1. user - FK to User
    2. type - FK to TransportCatalog
    3. desctiprion - text
    4. location - pin on the map
    # todo: need constraint for required amount of photos


## TransportPhoto:
    1. transport - FK to Transport


## TransportCatalogType:
    1. name

## TransportCatalogCategory:
    1. name

## TransportCatalog:
    1. type - FK to TransportCatalogType
    2. category - FK to TransportCatalogCategory
    3. name - unique
    4. icon - image of transport type
