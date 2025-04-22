import logging
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import os

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы состояний
CHOOSING, TYPING_REPLY = range(2)

# Токен бота
TOKEN = '8171259419:AAHUCx0YIDs2BqF32u1IoehgByrDqHNnee0'

# Вопросы по каждому опроснику
questionnaires = {
    "PHQ-9": {
        "title": "PHQ-9 — Оценка депрессии",
        "questions": [
            "Мало интереса или удовольствия от выполнения дел",
            "Чувство подавленности, депрессии или безнадежности",
            "Проблемы со сном (трудности засыпания, частые пробуждения или слишком долгое пребывание в постели)",
            "Чувство усталости или нехватки энергии",
            "Плохой аппетит или переедание",
            "Низкая самооценка (чувство, что вы подвели себя или свою семью)",
            "Трудности с концентрацией внимания на чтении газет или просмотре телевизора",
            "Замедленность движений или беспокойство, которое замечают другие",
            "Мысли о причинении себе вреда или что вам лучше умереть"
        ]
    },
    "GAD-7": {
        "title": "GAD-7 — Оценка тревожности",
        "questions": [
            "Чувство нервозности, тревожности или раздражительности",
            "Невозможность остановить или контролировать беспокойство",
            "Чрезмерное беспокойство по различным поводам",
            "Трудности в расслаблении",
            "Беспокойство настолько сильное, что сложно усидеть на месте",
            "Раздражительность",
            "Чувство, что что-то ужасное может случиться"
        ]
    },
    "PHQ-SADS": {
        "title": "PHQ-SADS — Комплексная шкала тревоги и депрессии",
        "questions": [
            "Чувство тревоги и страха",
            "Сильное волнение без причины",
            "Мысли, мешающие сосредоточиться",
            "Проблемы со сном из-за беспокойства",
            "Сильное раздражение без повода",
            "Чувство безнадежности",
            "Сложность чувствовать радость",
            "Мысли о собственной никчемности"
        ]
    },
    "ISI": {
        "title": "ISI — Индекс тяжести бессонницы",
        "questions": [
            "Трудности с засыпанием",
            "Трудности поддержания сна (частые пробуждения)",
            "Пробуждение раньше времени и невозможность заснуть снова",
            "Насколько вы довольны своим текущим сном",
            "Нарушение сна влияет на ваше функционирование в течение дня",
            "Нарушение сна заметно для окружающих",
            "Ваша обеспокоенность по поводу проблем со сном"
        ]
    }
}

# Интерпретации результатов
interpretations = {
    "PHQ-9": ["Минимальная депрессия (0–4)", "Легкая депрессия (5–9)", "Умеренная депрессия (10–14)", "Умеренно тяжелая депрессия (15–19)", "Тяжелая депрессия (20–27)"],
    "GAD-7": ["Минимальная тревожность (0–4)", "Легкая тревожность (5–9)", "Умеренная тревожность (10–14)", "Тяжелая тревожность (15–21)"],
    "PHQ-SADS": ["Низкий уровень симптомов (0–7)", "Умеренный уровень симптомов (8–14)", "Высокий уровень симптомов (15 и выше)"],
    "ISI": ["Нет бессонницы (0–7)", "Легкая бессонница (8–14)", "Умеренная бессонница (15–21)", "Тяжелая бессонница (22–28)"]
}

user_data = {}

# Объяснение шкалы ответов
scale_explanation = "Оцените каждый вопрос по шкале:\n0 — Совсем нет\n1 — Несколько дней\n2 — Более половины дней\n3 — Почти каждый день"

# Старт

def start(update: Update, context: CallbackContext):
    keyboard = [[key + f" — {questionnaires[key]['title']}"] for key in questionnaires]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Выберите опросник:", reply_markup=reply_markup)
    return CHOOSING

# Обработка выбора опросника

def choose_questionnaire(update: Update, context: CallbackContext):
    text = update.message.text
    key = text.split(" — ")[0]
    if key in questionnaires:
        context.user_data['current_test'] = key
        context.user_data['current_question'] = 0
        context.user_data['answers'] = []
        update.message.reply_text(f"Вы выбрали: {questionnaires[key]['title']}\n\n{scale_explanation}")
        return ask_question(update, context)
    else:
        update.message.reply_text("Пожалуйста, выберите опросник из списка.")
        return CHOOSING

# Задать вопрос

def ask_question(update: Update, context: CallbackContext):
    test = context.user_data['current_test']
    q_index = context.user_data['current_question']
    question = questionnaires[test]['questions'][q_index]
    reply_markup = ReplyKeyboardMarkup([["0", "1", "2", "3"]], one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(f"{q_index + 1}. {question}", reply_markup=reply_markup)
    return TYPING_REPLY

# Обработка ответа пользователя

def handle_answer(update: Update, context: CallbackContext):
    try:
        answer = int(update.message.text)
    except ValueError:
        update.message.reply_text("Пожалуйста, выберите цифру от 0 до 3.")
        return TYPING_REPLY

    context.user_data['answers'].append(answer)
    context.user_data['current_question'] += 1
    test = context.user_data['current_test']

    if context.user_data['current_question'] < len(questionnaires[test]['questions']):
        return ask_question(update, context)
    else:
        return finish_test(update, context)

# Завершение опроса и вывод результата

def finish_test(update: Update, context: CallbackContext):
    test = context.user_data['current_test']
    answers = context.user_data['answers']
    score = sum(answers)
    interpretation = ""
    for text in interpretations[test]:
        range_part = text.split("(")[1].replace(")", "")
        if '–' in range_part:
            min_val, max_val = map(int, range_part.split("–"))
        else:
            min_val = int(range_part.split()[0])
            max_val = 100
        if min_val <= score <= max_val:
            interpretation = text
            break

    result_text = f"Результаты по шкале {test} ({questionnaires[test]['title']}):\nСумма баллов: {score}\nИнтерпретация: {interpretation}"
    update.message.reply_text(result_text)

    filename = f"{test}_result.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(result_text)

    with open(filename, "rb") as f:
        update.message.reply_document(InputFile(f))

    os.remove(filename)

    # Предложить пройти следующий тест
    keyboard = [[key + f" — {questionnaires[key]['title']}"] for key in questionnaires if key != test]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Хотите пройти следующий опросник?", reply_markup=reply_markup)
    return CHOOSING

# Главная функция

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(Filters.text & ~Filters.command, choose_questionnaire)],
            TYPING_REPLY: [MessageHandler(Filters.text & ~Filters.command, handle_answer)]
        },
        fallbacks=[]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
