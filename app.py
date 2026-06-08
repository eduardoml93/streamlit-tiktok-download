# app.py
import streamlit as st
import requests
import re
import os
import tempfile
import base64
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="TikTok Video Downloader",
    page_icon="🎬",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .stApp {
        max-width: 1000px;
        margin: 0 auto;
    }
    .title {
        text-align: center;
        color: #FF0050;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .info-box {
        background-color: #e7f3ff;
        border: 1px solid #b3d7ff;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .download-btn {
        background-color: #FF0050 !important;
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        border-radius: 5px !important;
        font-size: 16px !important;
        cursor: pointer !important;
    }
    .progress-bar {
        height: 20px;
        background-color: #f0f0f0;
        border-radius: 10px;
        margin: 20px 0;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background-color: #FF0050;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Título da aplicação
st.markdown('<h1 class="title">🎬 TikTok Video Downloader</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Baixe vídeos do TikTok com um clique! Insira o link abaixo</p>', unsafe_allow_html=True)

def extract_video_info(url):
    """Extract username and video ID from TikTok URL"""
    try:
        pattern = r'tiktok\.com/@([^/]+)/video/(\d+)'
        match = re.search(pattern, url)
        
        if match:
            username = match.group(1)
            video_id = match.group(2)
            clean_username = username.split('?')[0].split('&')[0]
            return clean_username, video_id
        
        return None, None
        
    except Exception as e:
        return None, None

def normalize_url(video_url):
    """Ensure URL has proper protocol"""
    if video_url.startswith('//'):
        return 'https:' + video_url
    if not video_url.startswith('http'):
        return 'https://' + video_url
    return video_url

def extract_video_url_from_response(data, quality='hd'):
    """Extract video URL from API response based on quality preference"""
    video_url = None
    quality_label = 'Normal'

    if 'data' in data:
        api_data = data['data']
        if quality == 'hd' and api_data.get('hdplay'):
            video_url = api_data['hdplay']
            quality_label = 'HD'
        elif api_data.get('play'):
            video_url = api_data['play']
            quality_label = 'Normal'
        elif api_data.get('hdplay'):
            video_url = api_data['hdplay']
            quality_label = 'HD'

    elif 'video' in data and 'url' in data['video']:
        video_url = data['video']['url']
    elif 'url' in data:
        video_url = data['url']

    if video_url:
        return normalize_url(video_url), quality_label

    return None, None

def get_video_url_from_api(url, quality='hd'):
    """Get video URL from TikTok APIs"""
    api_services = [
        {
            'name': 'TikMate',
            'url': 'https://www.tikwm.com/api/',
            'method': 'POST',
            'params': {'url': url}
        },
        {
            'name': 'TikDown',
            'url': 'https://api.tikdown.org/api/download',
            'method': 'GET',
            'params': {'url': url}
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    
    for api in api_services:
        try:
            if api['method'] == 'POST':
                response = requests.post(api['url'], data=api['params'], headers=headers, timeout=30)
            else:
                response = requests.get(api['url'], params=api['params'], headers=headers, timeout=30)
            
            response.raise_for_status()
            data = response.json()
            
            video_url, quality_label = extract_video_url_from_response(data, quality)
            
            if video_url:
                return video_url, api['name'], quality_label
                
        except:
            continue
    
    return None, None, None

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Create a download link for binary file"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}" class="download-btn">⬇️ Baixar {file_label}</a>'
    return href

# Interface principal
url = st.text_input(
    "🔗 URL do TikTok:",
    placeholder="https://www.tiktok.com/@usuario/video/123456789...",
    help="Cole o link completo do vídeo do TikTok"
)

quality = st.radio(
    "🎞️ Qualidade do vídeo:",
    options=["hd", "normal"],
    format_func=lambda q: "HD (máxima qualidade)" if q == "hd" else "Normal",
    horizontal=True,
    help="HD oferece a melhor resolução disponível. Normal usa qualidade padrão."
)

col1, col2 = st.columns([3, 1])

with col1:
    st.caption("Escolha a qualidade acima e clique em baixar.")

with col2:
    download_btn = st.button("📥 Baixar Vídeo", type="primary", use_container_width=True)

# Barra de progresso placeholder
progress_bar = st.empty()

# Área para exibir resultados
result_placeholder = st.empty()

# Dicas úteis
with st.expander("💡 Como usar"):
    st.write("""
    1. Encontre o vídeo que deseja baixar no TikTok
    2. Clique em "Compartilhar" e depois em "Copiar link"
    3. Cole o link no campo acima
    4. Escolha a qualidade: **HD** ou **Normal**
    5. Clique em "Baixar Vídeo"
    6. Aguarde o processamento e clique no botão de download
    
    **Formato do arquivo:** O vídeo será salvo como `usuario_id.mp4` ou `usuario_id_hd.mp4`
    """)

# Quando o botão é clicado
if download_btn and url:
    with st.spinner("🔍 Analisando URL..."):
        # Extrair informações do vídeo
        username, video_id = extract_video_info(url)
        
        if not username or not video_id:
            result_placeholder.error("❌ URL inválida! Certifique-se de que é um link de vídeo do TikTok válido.")
            st.stop()
        
        quality_suffix = "_hd" if quality == "hd" else ""
        filename = f"{username}_{video_id}{quality_suffix}.mp4"
        quality_label = "HD (máxima qualidade)" if quality == "hd" else "Normal"
        
        # Mostrar informações
        result_placeholder.info(f"""
        **📋 Informações do vídeo:**
        - 👤 Usuário: @{username}
        - 🆔 ID do vídeo: {video_id}
        - 🎞️ Qualidade solicitada: {quality_label}
        - 💾 Nome do arquivo: `{filename}`
        """)
        
        # Atualizar barra de progresso
        progress_bar.progress(25, text="🔍 Buscando URL do vídeo...")
        
        # Obter URL do vídeo
        video_url, api_name, actual_quality = get_video_url_from_api(url, quality)
        
        if not video_url:
            result_placeholder.error("""
            ❌ Não foi possível encontrar o vídeo!
            
            **Possíveis causas:**
            1. O vídeo pode ser privado ou removido
            2. O TikTok pode estar bloqueado na sua região
            3. As APIs podem estar temporariamente indisponíveis
            
            **Soluções:**
            - Verifique se o vídeo é público
            - Tente com outro vídeo
            - Tente novamente mais tarde
            """)
            progress_bar.empty()
            st.stop()
        
        progress_bar.progress(50, text=f"✅ URL encontrada via {api_name}")
        
        # Download do vídeo
        try:
            progress_bar.progress(75, text="⬇️ Baixando vídeo...")
            
            video_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.tiktok.com/'
            }
            
            response = requests.get(video_url, headers=video_headers, stream=True, timeout=60)
            response.raise_for_status()
            
            # Salvar em arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            progress_bar.progress(100, text="✅ Vídeo baixado com sucesso!")
            
            # Exibir sucesso e botão de download
            result_placeholder.success(f"""
            🎉 **Download concluído com sucesso!**
            
            **📊 Detalhes:**
            - 📁 Arquivo: `{filename}`
            - 🎞️ Qualidade: {actual_quality}
            - 🔌 Fonte: {api_name}
            - 📤 Tamanho: {os.path.getsize(tmp_file_path):,} bytes
            
            Clique no botão abaixo para baixar o vídeo para seu computador:
            """)
            
            # Botão de download
            with open(tmp_file_path, 'rb') as file:
                st.download_button(
                    label=f"⬇️ Baixar {filename}",
                    data=file,
                    file_name=filename,
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True
                )
            
            # Preview do vídeo (opcional)
            with st.expander("🎥 Preview do vídeo"):
                st.video(tmp_file_path)
            
            # Limpar arquivo temporário após uso
            os.unlink(tmp_file_path)
            
        except Exception as e:
            result_placeholder.error(f"❌ Erro ao baixar o vídeo: {str(e)}")
            progress_bar.empty()
            
elif download_btn and not url:
    result_placeholder.warning("⚠️ Por favor, insira uma URL do TikTok")

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>⚠️ <strong>Aviso Legal:</strong> Use este aplicativo apenas para baixar vídeos que você tem permissão para usar.</p>
    <p>Respeite os direitos autorais e as políticas do TikTok.</p>
</div>

""", unsafe_allow_html=True)
