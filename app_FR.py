import streamlit as st
from swarm import Swarm, Agent
from duckduckgo_search import DDGS
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
#MODEL = "aya-expanse:latest"
MODEL = "aya-expanse:8b-q8_0"

# Initialize Swarm client
client = Swarm()

ddgs = DDGS()

# Search the web for the given query
def search_web(query):
    DDG_MODE = "text" ## text OR news
    
    print(f"DDG Mode : {DDG_MODE}")
    print(f"Recherche sur le Web pour : {query}...")
    
    # DuckDuckGo search
    if DDG_MODE == 'text':
        ## Mode Texte
        current_date = datetime.now().strftime("%Y-%m")
        results      = ddgs.text(f"{query} {current_date}", region='fr-fr', max_results=10)

    elif DDG_MODE == 'news':    
        ## Mode News (Actualités)
        results      = ddgs.news(f"{query}", region='fr-fr', timelimit='m', max_results=10)
        #{
        #    'date': '2024-10-31T07:02:00+00:00',
        #    'title': 'Les 5 principales différences entre les R5 E-Tech et la nouvelle R4',
        #    'body': "Cette année, deux grosses nouveautés électriques ont fait leur apparition au Mondial de l'Auto, la R5, dévoilée il y a déjà six mois, et la nouvelle R4, un nouveau petit SUV. Très proches techniquemen",
        #    'url': 'https://www.planeterenault.com/1-gamme/8-futures/1597-actualite-automobile/12372--5-principales-differences-entre-r5-e-tech-et-nouvelle-r4/',
        #    'image': '',
        #    'source': 'planeterenault.com'
        #}

    else:
        print(f"DDG_MODE ERROR : {DDG_MODE} is not equal to 'text' or 'news'")
        exit(1)

    if results:
        news_results = ""
    
        for result in results:
            if DDG_MODE == 'text':
                news_results += f"Titre: {result['title']}\nURL: {result['href']}\nDescription: {result['body']}\n\n"
            elif DDG_MODE == "news":
                news_results += f"Titre: {result['title']}\nURL: {result['url']}\nDescription: {result['body']}\n\n"
    
        return news_results.strip()
    
    else:
        return f"N'a pas pu trouver de résultat à propos de {query}."
    

# Web Search Agent to fetch latest news
web_search_agent = Agent(
    name         = "Assistant de recherche sur le Web",
    model        = MODEL,
    instructions = "Votre rôle est de rassembler les derniers articles d'actualité sur des sujets spécifiques en utilisant les capacités de recherche de DuckDuckGo.",
    functions    = [search_web]
)

# Senior Research Analyst 
researcher_agent = Agent(
    name         = "Assistant de Recherches",
    model        = MODEL,
    instructions = """Votre rôle est d'analyser et de synthétiser les résultats de recherche bruts. Vous devez :
    1. Supprimer les informations en double et le contenu redondant
    2. Identifier et fusionner les sujets et thèmes connexes
    3. Vérifier la cohérence des informations entre les sources
    4. Prioriser les informations récentes et pertinentes
    5. Extraire les faits, statistiques et citations clés
    6. Identifier les sources primaires lorsqu'elles sont disponibles
    7. Signaler toute information contradictoire
    8. Maintenir une attribution appropriée pour les affirmations importantes
    9. Organiser les informations dans une séquence logique
    10. Préserver le contexte important et les relations entre les sujets"""
)

# Editor Agent to edit news
writer_agent = Agent(
    name         = "Assistant Rédacteur",
    model        = MODEL,
    instructions = """Votre rôle est de transformer les résultats de recherche dédupliqués en un article soigné et prêt à être publié. Vous devez :
    1. Organiser le contenu en sections claires et thématiques
    2. Écrire sur un ton professionnel mais engageant, authentique et informatif
    3. Assurer une bonne fluidité entre les sujets
    4. Ajouter un contexte pertinent si nécessaire
    5. Maintenir l'exactitude des faits tout en rendant les sujets complexes accessibles
    6. Inclure un bref résumé au début
    7. Formater avec des titres et des sous-titres clairs
    8. Conserver toutes les informations clés du matériel source"""
)

# Create and run the workflow
def run_workflow(query):
    print("Exécution du flux de travail de l'Assistant de recherche Web...")
    
    # Search the web
    news_response = client.run(
        agent    = web_search_agent,
        messages = [{"role": "user", "content": f"Fais une recherche sur le Web pour : {query}"}],
    )
    
    raw_news = news_response.messages[-1]["content"]

    # Analyze and synthesize the search results
    research_analysis_response = client.run(
        agent    = researcher_agent,
        messages = [{"role": "user", "content": raw_news }],
    )

    deduplicated_news = research_analysis_response.messages[-1]["content"]
    
    # Edit and publish the analysed results with streaming
    return client.run(
        agent    = writer_agent,
        messages = [{"role": "user", "content": deduplicated_news }],
        stream   = True  # Enable streaming
    )

# Streamlit app
def main():
    st.set_page_config(page_title="Assistant Internet 🔎", page_icon="🔎")
    st.title("Assistant de Recherches pour Internet - FR - 🔎")

    # Initialize session state for query and article
    if 'query' not in st.session_state:
        st.session_state.query = ""
    if 'article' not in st.session_state:
        st.session_state.article = ""

    # Create two columns for the input and clear button
    col1, col2 = st.columns([3, 1])

    # Search query input
    with col1:
        query = st.text_input("Entrez votre requête:", value=st.session_state.query)

    # Clear button
    with col2:
        if st.button("Effacer"):
            st.session_state.query = ""
            st.session_state.article = ""
            print("CLEAR")
            st.rerun()

    # Generate article only when button is clicked
    if st.button("Génerer un Article") and query:
        with st.spinner("Generation de l'article..."):
            # Get streaming response
            streaming_response = run_workflow(query)
            st.session_state.query = query
            
            # Create a placeholder for the streaming text
            message_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            for chunk in streaming_response:
                # Skip the initial delimiter
                if isinstance(chunk, dict) and 'delim' in chunk:
                    continue
                    
                # Extract only the content from each chunk
                if isinstance(chunk, dict) and 'content' in chunk:
                    content = chunk['content']
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            # Update final response
            print("Article Ok : displaying...")
            message_placeholder.markdown(full_response)
            st.session_state.article = full_response
            print("Fin.")

if __name__ == "__main__":
    main()
