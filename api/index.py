from final_app import app

# Vercel entry point
@app.route('/')
def index():
    """Route racine pour Vercel"""
    from final_app import load_radios
    radios = load_radios()
    from flask import render_template
    return render_template('index.html', stations=radios)

if __name__ == "__main__":
    app.run()
