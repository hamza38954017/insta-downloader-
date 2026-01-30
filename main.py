from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp
import requests

app = Flask(__name__)

# --- THE WEBSITE DESIGN (HTML/CSS/JS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InstaGlow Mobile</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @keyframes gradient-xy {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        .animate-gradient {
            background-size: 200% 200%;
            animation: gradient-xy 6s ease infinite;
        }
        .glass {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            -webkit-backdrop-filter: blur(16px);
        }
    </style>
</head>
<body class="bg-black text-white min-h-screen flex flex-col items-center justify-center relative overflow-hidden font-sans">

    <div class="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-gray-900 via-black to-gray-900 z-0"></div>
    <div class="absolute top-[-50px] left-[-50px] w-64 h-64 bg-purple-600 rounded-full mix-blend-screen filter blur-3xl opacity-20 animate-pulse"></div>
    <div class="absolute bottom-[-50px] right-[-50px] w-64 h-64 bg-pink-600 rounded-full mix-blend-screen filter blur-3xl opacity-20 animate-pulse"></div>

    <div class="glass relative z-10 w-full max-w-lg p-6 md:p-10 m-4 rounded-3xl shadow-2xl border-t border-gray-700">
        
        <div class="text-center mb-8">
            <h1 class="text-5xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 mb-2">
                InstaFlow
            </h1>
            <p class="text-gray-400 text-sm">High Quality Video Downloader</p>
        </div>

        <div class="relative group mb-6">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-pink-600 to-purple-600 rounded-xl blur opacity-30 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
            <div class="relative flex items-center bg-gray-900 rounded-xl leading-none">
                <input type="text" id="urlInput" placeholder="Paste Instagram Link Here..." 
                    class="w-full p-4 bg-transparent text-gray-200 placeholder-gray-600 focus:outline-none text-base">
                <button onclick="fetchInfo()" class="pr-4 pl-2 text-purple-400 hover:text-white transition-colors">
                    <i class="fas fa-arrow-right text-xl"></i>
                </button>
            </div>
        </div>

        <div id="loader" class="hidden flex flex-col items-center justify-center my-8 space-y-2">
            <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
            <span class="text-xs text-purple-400 animate-pulse">Fetching video info...</span>
        </div>

        <div id="resultArea" class="hidden transform transition-all duration-500 ease-out translate-y-4 opacity-0">
            <div class="bg-gray-800/50 rounded-2xl overflow-hidden shadow-xl border border-gray-700/50">
                <div class="relative aspect-video bg-black">
                    <img id="thumb" src="" alt="Thumbnail" class="w-full h-full object-contain opacity-90">
                    <div class="absolute bottom-2 right-2 bg-black/70 px-2 py-1 rounded text-xs text-white font-mono">
                        HD
                    </div>
                </div>
                
                <div class="p-4">
                    <h3 id="vidTitle" class="text-sm font-medium text-gray-300 line-clamp-1 mb-4"></h3>
                    
                    <a id="downloadBtn" href="#" 
                        class="flex items-center justify-center w-full py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg shadow-purple-900/20 transition-all active:scale-95">
                        <i class="fas fa-download mr-2"></i> Download Video
                    </a>
                </div>
            </div>
        </div>
        
        <div id="errorMsg" class="hidden mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg text-center">
            <p class="text-red-400 text-sm flex items-center justify-center gap-2">
                <i class="fas fa-exclamation-circle"></i> <span id="errorText">Error</span>
            </p>
        </div>

        <div class="mt-8 text-center">
            <p class="text-xs text-gray-600">Free service running on Render</p>
        </div>

    </div>

    <script>
        async function fetchInfo() {
            const url = document.getElementById('urlInput').value.trim();
            const loader = document.getElementById('loader');
            const resultArea = document.getElementById('resultArea');
            const errorMsg = document.getElementById('errorMsg');
            const resultDiv = document.getElementById('resultArea');

            if (!url) return;

            // Reset UI
            resultDiv.classList.add('hidden', 'opacity-0', 'translate-y-4');
            resultDiv.classList.remove('opacity-100', 'translate-y-0');
            errorMsg.classList.add('hidden');
            loader.classList.remove('hidden');

            try {
                const response = await fetch('/get-info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await response.json();

                if (data.status === 'success') {
                    document.getElementById('thumb').src = data.thumbnail;
                    document.getElementById('vidTitle').innerText = data.title;
                    
                    // Construct download link
                    const cleanTitle = (data.title || 'video').replace(/[^a-zA-Z0-9]/g, "_").substring(0, 50);
                    const downloadLink = `/download?url=${encodeURIComponent(data.direct_url)}&title=${cleanTitle}`;
                    document.getElementById('downloadBtn').href = downloadLink;

                    // Show result with animation
                    loader.classList.add('hidden');
                    resultDiv.classList.remove('hidden');
                    // Small delay to allow display:block to apply before animating opacity
                    setTimeout(() => {
                        resultDiv.classList.remove('opacity-0', 'translate-y-4');
                        resultDiv.classList.add('opacity-100', 'translate-y-0');
                    }, 50);

                } else {
                    throw new Error(data.message || "Invalid Link");
                }
            } catch (e) {
                loader.classList.add('hidden');
                document.getElementById('errorText').innerText = "Failed: Check link or try again.";
                errorMsg.classList.remove('hidden');
            }
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        # User-Agent is important for Instagram
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'status': 'success',
                'title': info.get('title', 'Instagram Video'),
                'thumbnail': info.get('thumbnail'),
                'direct_url': info.get('url'),
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.route('/')
def home():
    # Renders the HTML string defined above
    return render_template_string(HTML_TEMPLATE)

@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'status': 'error', 'message': 'No URL provided'})
    
    info = get_video_info(url)
    return jsonify(info)

@app.route('/download')
def download_video():
    video_url = request.args.get('url')
    title = request.args.get('title', 'insta_video')
    
    if not video_url:
        return "Error: Link missing", 400

    # Stream the file to avoid storage issues on Render
    try:
        req = requests.get(video_url, stream=True)
        return Response(
            stream_with_context(req.iter_content(chunk_size=1024)),
            content_type=req.headers.get('content-type', 'video/mp4'),
            headers={
                'Content-Disposition': f'attachment; filename="{title}.mp4"'
            }
        )
    except Exception as e:
        return f"Download failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
