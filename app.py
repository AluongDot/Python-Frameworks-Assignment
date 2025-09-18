
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="CORD-19 Data Explorer",
    page_icon=":bar_chart:",
    layout="wide"
)

# Title and description
st.title("CORD-19 COVID-19 Research Data Explorer")
st.write("""
This interactive dashboard explores the CORD-19 dataset containing metadata about COVID-19 research papers.
Use the filters below to explore different aspects of the data.
""")

# Load data - try cleaned data first, then original data
@st.cache_data
def load_data():
    try:
        # First try to load the cleaned data
        df = pd.read_csv('cleaned_metadata.csv', low_memory=False)
        st.success("Loaded cleaned_metadata.csv successfully!")
    except:
        try:
            # If cleaned data not available, try original data with basic cleaning
            st.info("cleaned_metadata.csv not found. Trying to load metadata.csv...")
            df = pd.read_csv('metadata.csv', low_memory=False)
            # Add basic cleaning
            df = df.dropna(subset=['title'])
            df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')
            df['publication_year'] = df['publish_time'].dt.year
            df = df[(df['publication_year'] >= 2019) & (df['publication_year'] <= datetime.now().year)]
            df['abstract'] = df['abstract'].fillna('')
            if 'journal' in df.columns:
                df['journal'] = df['journal'].fillna('Unknown').str.title()
            st.success("Loaded metadata.csv with basic cleaning!")
        except:
            st.error("Could not load data. Please ensure either metadata.csv or cleaned_metadata.csv is available.")
            # Create sample data for demonstration
            data = {
                'title': ['COVID-19 Research Paper 1', 'Study on Coronavirus 2', 'SARS-CoV-2 Analysis'],
                'abstract': ['Abstract text 1 about coronavirus and pandemic', 
                            'Abstract text 2 about vaccines and treatment', 
                            'Abstract text 3 about social distancing measures'],
                'publish_time': ['2020-03-15', '2020-04-20', '2021-01-10'],
                'journal': ['Journal of Medicine', 'Lancet', 'Nature'],
                'publication_year': [2020, 2020, 2021]
            }
            df = pd.DataFrame(data)
            st.info("Using sample data for demonstration.")

    return df

df = load_data()

if not df.empty:
    # Sidebar filters
    st.sidebar.header("Filters")

    # Year range selector
    if 'publication_year' in df.columns:
        min_year = int(df['publication_year'].min())
        max_year = int(df['publication_year'].max())
        year_range = st.sidebar.slider(
            "Select publication year range:",
            min_year, max_year, (min_year, max_year)
        )
    else:
        year_range = (2019, 2023)
        st.sidebar.info("Year data not available")

    # Journal selector (if available)
    if 'journal' in df.columns:
        journals = ['All'] + sorted(df['journal'].dropna().unique().tolist()[:20])
        selected_journal = st.sidebar.selectbox("Select journal:", journals)
    else:
        selected_journal = 'All'
        st.sidebar.info("Journal data not available")

    # Abstract word count filter
    min_words, max_words = st.sidebar.slider(
        "Abstract word count range:",
        0, 1000, (0, 500)
    )

    # Filter data based on selections
    filtered_df = df.copy()

    if 'publication_year' in df.columns:
        filtered_df = filtered_df[
            (filtered_df['publication_year'] >= year_range[0]) & 
            (filtered_df['publication_year'] <= year_range[1])
        ]

    if 'journal' in df.columns and selected_journal != 'All':
        filtered_df = filtered_df[filtered_df['journal'] == selected_journal]

    # Add abstract word count for filtering
    filtered_df['abstract_word_count'] = filtered_df['abstract'].apply(lambda x: len(str(x).split()))
    filtered_df = filtered_df[
        (filtered_df['abstract_word_count'] >= min_words) & 
        (filtered_df['abstract_word_count'] <= max_words)
    ]

    # Main content
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Overview")
        st.metric("Total Papers", len(filtered_df))

        if 'journal' in filtered_df.columns:
            st.metric("Unique Journals", filtered_df['journal'].nunique())
        else:
            st.metric("Unique Journals", "N/A")

        st.metric("Average Abstract Length", f"{filtered_df['abstract_word_count'].mean():.1f} words")

        # Papers by year chart (if year data available)
        if 'publication_year' in filtered_df.columns:
            yearly_counts = filtered_df['publication_year'].value_counts().sort_index()
            st.subheader("Papers by Year")
            fig, ax = plt.subplots(figsize=(10, 4))
            yearly_counts.plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title("Publications by Year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Number of Papers")
            plt.xticks(rotation=45)
            st.pyplot(fig)

    with col2:
        # Top journals (if journal data available)
        if 'journal' in filtered_df.columns:
            top_journals = filtered_df['journal'].value_counts().head(10)
            st.subheader("Top Journals")
            fig, ax = plt.subplots(figsize=(10, 4))
            top_journals.plot(kind='bar', ax=ax, color='lightcoral')
            ax.set_title("Top 10 Journals")
            ax.set_xlabel("Journal")
            ax.set_ylabel("Number of Papers")
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)

        # Abstract length distribution
        st.subheader("Abstract Length Distribution")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(filtered_df['abstract_word_count'], bins=30, color='purple', alpha=0.7, edgecolor='black')
        ax.set_title("Abstract Word Count Distribution")
        ax.set_xlabel("Word Count")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)

    # Word frequency instead of word cloud
    st.subheader("Top Words in Titles")
    if not filtered_df.empty and 'title' in filtered_df.columns:
        # Combine all titles
        all_titles = ' '.join(filtered_df['title'].dropna().astype(str))

        # Remove common words and clean text
        stop_words = {'the', 'and', 'of', 'in', 'to', 'a', 'for', 'on', 'with', 'by', 'an', 'as', 'at'}
        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_titles.lower())
        filtered_words = [word for word in words if word not in stop_words]

        # Count word frequency
        word_freq = pd.Series(filtered_words).value_counts().head(15)

        fig, ax = plt.subplots(figsize=(10, 5))
        word_freq.plot(kind='bar', ax=ax, color='lightgreen')
        ax.set_title("Top Words in Titles")
        ax.set_xlabel("Words")
        ax.set_ylabel("Frequency")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    # Sample data
    st.subheader("Sample Data")

    # Select which columns to show
    display_columns = ['title']
    if 'journal' in filtered_df.columns:
        display_columns.append('journal')
    if 'publication_year' in filtered_df.columns:
        display_columns.append('publication_year')
    display_columns.append('abstract_word_count')

    st.dataframe(filtered_df[display_columns].head(10))

    # Download button for filtered data
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name="filtered_cord19_data.csv",
        mime="text/csv"
    )

else:
    st.warning("No data available. Please check your data file.")

st.sidebar.markdown("---")
st.sidebar.info("""
**About this app:**
This app provides basic exploration of the CORD-19 dataset containing COVID-19 research papers metadata.
""")
