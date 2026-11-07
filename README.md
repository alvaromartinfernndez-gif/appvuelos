# Buscador de Escapadas Económicas

A small Streamlit app for exploring sample weekend-flight prices by budget or destination. The flight data is currently hard-coded demo data; it does not yet connect to a live flight API.

## Run locally

1. Install Python 3.9 or newer.
2. In a terminal, from this repository's directory, install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the app:

   ```bash
   streamlit run app.py
   ```

Streamlit will print a local URL (usually http://localhost:8501) to open in your browser.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) using GitHub and authorize access to this repository.
3. Choose **Create app**, select `alvaromartinfernndez-gif/appvuelos`, choose the `main` branch, and set the app file path to `app.py`.
4. Click **Deploy**. Streamlit will install the packages listed in `requirements.txt`.

After deployment, the app will have a shareable URL. When you push changes to the selected GitHub branch, Streamlit will redeploy the app.
