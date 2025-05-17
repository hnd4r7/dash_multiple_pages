import dash
import dash_html_components as html
import dash_uploader as du

app = dash.Dash(__name__)

# Configure the base upload folder with use_upload_id=True
du.configure_upload(app, folder="intermediate", use_upload_id=True)

# Create layout with multiple upload components
app.layout = html.Div(
    [
        html.H3("Upload 1"),
        du.Upload(id="upload1", upload_id="iii/p pp"),
        html.H3("Upload 2"),
        du.Upload(id="upload2", upload_id="kkk/oo o"),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
