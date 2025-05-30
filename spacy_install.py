import spacy
import nltk
from nltk.stem.snowball import SnowballStemmer

# Lade NLTK-Tokenizer-Ressourcen
nltk.download('punkt')

# Liste der benötigten spaCy-Modelle
models = [
    "de_core_news_sm",
    "en_core_web_sm",
    "fr_core_news_sm",
    "es_core_news_sm",
    "ja_core_news_sm",
    "it_core_news_sm",
    "pt_core_news_sm",
    "el_core_news_sm",
    "nl_core_news_sm",
    "sv_core_news_sm",
    "nb_core_news_sm",
    "da_core_news_sm",
    "fi_core_news_sm",
    "pl_core_news_sm",
    "xx_ent_wiki_sm",
    "ro_core_news_sm",
    "hr_core_news_sm",
    "ru_core_news_sm",
    "uk_core_news_sm"
]


# Lade alle spaCy-Modelle herunter
for model in models:
    print(f"Lade Modell: {model}")
    spacy.cli.download(model)

 