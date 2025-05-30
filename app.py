import streamlit as st
import google.generativeai as genai
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import json
import time
import datetime
import re
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="LinkedIn Post Generator Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for professional styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        text-align: center;
        padding: 3rem 0;
        background: linear-gradient(135deg, #0077b5 0%, #00a0dc 50%, #0066cc 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,119,181,0.3);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    .post-container {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e3e6ea;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        position: relative;
        overflow: hidden;
    }
    
    .post-container::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        width: 4px;
        background: linear-gradient(180deg, #0077b5, #00a0dc);
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e1e5e9;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: transform 0.2s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #0077b5, #00a0dc);
        color: white;
        border: none;
        padding: 0.7rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,119,181,0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #005885, #0077b5);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,119,181,0.4);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e1e5e9;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0077b5;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        font-weight: 500;
    }
    
    .analytics-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e1e5e9;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    .success-message {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border: 1px solid #ffeaa7;
    }
    
    .pro-tip {
        background: linear-gradient(135deg, #cce5ff 0%, #e6f3ff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #0077b5;
        margin: 1rem 0;
    }
    
    .engagement-score {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin: 0.5rem 0;
    }
    
    .tab-container {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# Data classes for better organization
@dataclass
class PostMetrics:
    character_count: int
    word_count: int
    hashtag_count: int
    engagement_score: float
    readability_score: str

@dataclass
class PostTemplate:
    name: str
    description: str
    structure: str
    example: str

# Enhanced templates
POST_TEMPLATES = {
    "Industry Insight": PostTemplate(
        name="Industry Insight",
        description="Share professional insights and trends",
        structure="Hook → Insight → Evidence → Call to Action",
        example="🚀 The remote work revolution isn't slowing down...\n\nHere's what the latest data reveals about the future of work..."
    ),
    "Personal Story": PostTemplate(
        name="Personal Story",
        description="Share personal experiences and lessons",
        structure="Story Setup → Challenge → Resolution → Lesson",
        example="Yesterday, I made a mistake that taught me more than any success...\n\nHere's what happened and what I learned..."
    ),
    "Educational Content": PostTemplate(
        name="Educational Content",
        description="Teach something valuable to your audience",
        structure="Problem → Solution Steps → Benefits → Resources",
        example="Struggling with productivity? Here are 5 science-backed methods that actually work..."
    ),
    "Question/Poll": PostTemplate(
        name="Question/Poll",
        description="Engage audience with questions",
        structure="Context → Question → Options → Engagement Ask",
        example="I've been thinking about the future of AI in our industry...\n\nWhat's your biggest concern? 👇"
    ),
    "Achievement/Milestone": PostTemplate(
        name="Achievement/Milestone",
        description="Share wins and celebrate progress",
        structure="Achievement → Journey → Gratitude → Future Goals",
        example="🎉 Just hit a major milestone that seemed impossible 12 months ago...\n\nHere's how it happened..."
    ),
    "Controversial Take": PostTemplate(
        name="Controversial Take",
        description="Share bold opinions respectfully",
        structure="Unpopular Opinion → Reasoning → Evidence → Discussion Invite",
        example="Unpopular opinion: The 40-hour work week is dead, and here's why that's actually good news..."
    )
}

# Initialize session state
def init_session_state():
    if 'post_history' not in st.session_state:
        st.session_state.post_history = []
    if 'generated_post' not in st.session_state:
        st.session_state.generated_post = ""
    if 'current_template' not in st.session_state:
        st.session_state.current_template = None
    if 'analytics_data' not in st.session_state:
        st.session_state.analytics_data = []

def calculate_post_metrics(post_text: str) -> PostMetrics:
    """Calculate comprehensive metrics for a post"""
    char_count = len(post_text)
    word_count = len(post_text.split())
    hashtag_count = len(re.findall(r'#\w+', post_text))
    
    # Simple engagement score calculation
    engagement_factors = {
        'question_marks': post_text.count('?') * 2,
        'exclamation_marks': post_text.count('!') * 1.5,
        'emojis': len(re.findall(r'[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]', post_text)) * 1.2,
        'call_to_action': 3 if any(cta in post_text.lower() for cta in ['what do you think', 'comment below', 'share your', 'let me know']) else 0,
        'optimal_length': 5 if 100 <= char_count <= 1300 else 0,
        'hashtags': min(hashtag_count * 0.5, 4)  # Cap at 4 points for hashtags
    }
    
    engagement_score = min(sum(engagement_factors.values()) / 2, 10)  # Scale to 10
    
    # Readability assessment
    sentences = len(re.split(r'[.!?]+', post_text))
    avg_words_per_sentence = word_count / max(sentences, 1)
    
    if avg_words_per_sentence <= 15:
        readability = "Excellent"
    elif avg_words_per_sentence <= 20:
        readability = "Good"
    elif avg_words_per_sentence <= 25:
        readability = "Fair"
    else:
        readability = "Needs Improvement"
    
    return PostMetrics(
        character_count=char_count,
        word_count=word_count,
        hashtag_count=hashtag_count,
        engagement_score=engagement_score,
        readability_score=readability
    )

def generate_content_with_template(api_key: str, template: PostTemplate, user_input: str, settings: dict) -> str:
    """Generate content using selected template and user input"""
    genai.configure(api_key=api_key)
    
    prompt = f"""
    Create a LinkedIn post using the "{template.name}" template structure: {template.structure}
    
    User Input: {user_input}
    
    Settings:
    - Tone: {settings['tone']}
    - Length: {settings['length']}
    - Industry Focus: {settings.get('industry', 'General')}
    - Target Audience: {settings.get('audience', 'LinkedIn professionals')}
    
    Requirements:
    - Follow the template structure closely
    - Make it highly engaging and valuable
    - Use appropriate emojis strategically (2-4 total)
    - Use line breaks for readability
    - Write in a conversational yet professional tone
    {'- Include 5-8 relevant hashtags at the end' if settings['hashtags'] else '- No hashtags'}
    {'- Include a clear call-to-action' if settings['cta'] else '- No call-to-action needed'}
    
    Make it authentic and compelling for LinkedIn's professional audience.
    """
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

def create_post_image(text: str, template_style: str = "professional") -> Image.Image:
    """Create a simple branded image for the post"""
    # Create a simple branded image
    img = Image.new('RGB', (1200, 630), color='#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        subtitle_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Add LinkedIn brand colors gradient effect
    for i in range(630):
        color_ratio = i / 630
        r = int(0 + (248-0) * color_ratio)
        g = int(119 + (249-119) * color_ratio)
        b = int(181 + (250-181) * color_ratio)
        draw.line([(0, i), (1200, i)], fill=(r, g, b))
    
    # Add text
    title = "LinkedIn Post"
    subtitle = "Generated with AI"
    
    # Calculate text positions
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (1200 - title_width) // 2
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (1200 - subtitle_width) // 2
    
    # Draw text with shadow effect
    draw.text((title_x+2, 282), title, font=title_font, fill='#333333')
    draw.text((title_x, 280), title, font=title_font, fill='white')
    
    draw.text((subtitle_x+2, 332), subtitle, font=subtitle_font, fill='#666666')
    draw.text((subtitle_x, 330), subtitle, font=subtitle_font, fill='white')
    
    return img

# Main application
def main():
    init_session_state()
    
    # Header with enhanced styling
    st.markdown("""
    <div class="main-header">
        <h1>🚀 LinkedIn Post Generator Pro</h1>
        <p>AI-Powered Content Creation with Advanced Analytics & Templates</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Google AI Studio API Key", 
            type="password",
            help="Get your free API key from https://aistudio.google.com/app/apikey"
        )
        
        if not api_key:
            st.markdown("""
            <div class="warning-message">
                <strong>⚠️ API Key Required</strong><br>
                Please enter your Google AI Studio API key to continue
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔑 How to get your API key"):
                st.markdown("""
                **Step-by-step guide:**
                1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
                2. Sign in with your Google account
                3. Click **'Create API Key'**
                4. Copy and paste it above
                
                **Free Tier Benefits:**
                - ✅ 15 requests per minute
                - ✅ 1,500 requests per day
                - ✅ 1 million tokens per minute
                - ✅ No credit card required
                """)
        
        st.divider()
        
        # Enhanced post customization
        st.header("🎨 Content Settings")
        
        # Template selection
        template_name = st.selectbox(
            "📝 Post Template",
            list(POST_TEMPLATES.keys()),
            help="Choose a proven template structure"
        )
        
        selected_template = POST_TEMPLATES[template_name]
        
        with st.expander(f"📋 About {template_name} Template"):
            st.write(f"**Description:** {selected_template.description}")
            st.write(f"**Structure:** {selected_template.structure}")
            st.code(selected_template.example, language=None)
        
        # Advanced settings
        col1, col2 = st.columns(2)
        with col1:
            post_tone = st.selectbox(
                "🎭 Tone",
                ["Professional", "Casual", "Inspirational", "Educational", "Humorous", "Thought-provoking", "Conversational"]
            )
        
        with col2:
            post_length = st.selectbox(
                "📏 Length",
                ["Short (100-300 chars)", "Medium (300-800 chars)", "Long (800-1300 chars)", "Extended (1300+ chars)"]
            )
        
        # Industry and audience
        industry = st.selectbox(
            "🏢 Industry Focus",
            ["General", "Technology", "Marketing", "Sales", "HR", "Finance", "Healthcare", "Education", 
             "Consulting", "Real Estate", "Manufacturing", "Retail", "Startup"]
        )
        
        target_audience = st.selectbox(
            "🎯 Target Audience",
            ["All Professionals", "Entry Level", "Mid-Level", "Senior Level", "Executives", "Entrepreneurs", 
             "Job Seekers", "Students", "Freelancers"]
        )
        
        # Feature toggles
        st.subheader("⚙️ Features")
        include_hashtags = st.checkbox("Include Hashtags", value=True)
        include_cta = st.checkbox("Include Call-to-Action", value=True)
        include_emojis = st.checkbox("Include Emojis", value=True)
        generate_image = st.checkbox("Generate Post Image", value=False)
        
        # Analytics toggle
        show_analytics = st.checkbox("Show Advanced Analytics", value=True)

    # Main content area
    if api_key:
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["✍️ Create Post", "📊 Analytics", "📚 Post History", "🎓 Learning Hub"])
        
        with tab1:
            # Post creation interface
            st.header("💡 Create Your LinkedIn Post")
            
            # Input method selection
            input_method = st.radio(
                "Choose your input method:",
                ["💭 Topic/Idea", "📝 Key Points", "📰 Article/News", "🎯 Custom Prompt"],
                horizontal=True
            )
            
            user_input = ""
            
            if input_method == "💭 Topic/Idea":
                col1, col2 = st.columns([2, 1])
                with col1:
                    topic = st.text_input(
                        "Enter your topic or main idea:",
                        placeholder="e.g., Remote work productivity, AI in healthcare, Career pivot strategies..."
                    )
                with col2:
                    quick_topics = st.selectbox(
                        "Quick Topics",
                        ["", "Career Growth", "Leadership", "Innovation", "Work-Life Balance", 
                         "Team Management", "Digital Transformation", "Networking"]
                    )
                    if quick_topics:
                        topic = quick_topics
                
                additional_context = st.text_area(
                    "Additional context or your unique perspective:",
                    placeholder="Share your personal experience, insights, or specific angle on this topic..."
                )
                user_input = f"Topic: {topic}\nContext: {additional_context}"
                
            elif input_method == "📝 Key Points":
                key_points = st.text_area(
                    "Enter key points (one per line):",
                    placeholder="• First key insight or takeaway\n• Second important point\n• Supporting evidence or example\n• Conclusion or action item",
                    height=150
                )
                user_input = f"Key points to cover:\n{key_points}"
                
            elif input_method == "📰 Article/News":
                col1, col2 = st.columns([2, 1])
                with col1:
                    article_url = st.text_input("Article URL (optional):")
                with col2:
                    article_type = st.selectbox("Content Type", ["Article", "News", "Research", "Report", "Blog Post"])
                
                article_summary = st.text_area(
                    f"{article_type} summary or key insights:",
                    placeholder="Summarize the main points and share your perspective on what this means for your industry...",
                    height=120
                )
                user_input = f"{article_type} insights: {article_summary}"
                if article_url:
                    user_input += f"\nSource: {article_url}"
                    
            else:  # Custom Prompt
                custom_prompt = st.text_area(
                    "Enter your custom prompt:",
                    placeholder="Write a detailed prompt describing exactly what kind of post you want to create...",
                    height=120
                )
                user_input = custom_prompt
            
            # Settings summary
            settings = {
                'tone': post_tone,
                'length': post_length,
                'industry': industry,
                'audience': target_audience,
                'hashtags': include_hashtags,
                'cta': include_cta,
                'emojis': include_emojis
            }
            
            # Generate button with enhanced styling
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Generate LinkedIn Post", key="generate_btn", use_container_width=True):
                    if user_input.strip():
                        with st.spinner("🤖 AI is crafting your perfect LinkedIn post..."):
                            try:
                                generated_content = generate_content_with_template(
                                    api_key, selected_template, user_input, settings
                                )
                                st.session_state.generated_post = generated_content
                                
                                # Add to history
                                post_data = {
                                    'timestamp': datetime.datetime.now(),
                                    'template': template_name,
                                    'content': generated_content,
                                    'settings': settings,
                                    'input': user_input
                                }
                                st.session_state.post_history.append(post_data)
                                
                                st.markdown("""
                                <div class="success-message">
                                    ✅ <strong>Post Generated Successfully!</strong><br>
                                    Your LinkedIn post is ready for review and editing.
                                </div>
                                """, unsafe_allow_html=True)
                                
                            except Exception as e:
                                st.error(f"❌ Error generating post: {str(e)}")
                                st.info("💡 Please check your API key and try again.")
                    else:
                        st.warning("⚠️ Please provide input for your post.")
            
            # Display generated content
            if st.session_state.generated_post:
                st.divider()
                
                # Post preview with metrics
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.header("📝 Generated Post")
                    
                    # Post container with enhanced styling
                    st.markdown('<div class="post-container">', unsafe_allow_html=True)
                    
                    # Editable post content
                    edited_post = st.text_area(
                        "Edit your post:",
                        value=st.session_state.generated_post,
                        height=300,
                        key="post_editor"
                    )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    if show_analytics:
                        st.header("📊 Post Metrics")
                        metrics = calculate_post_metrics(edited_post)
                        
                        # Metrics display
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{metrics.character_count}</div>
                            <div class="metric-label">Characters</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{metrics.word_count}</div>
                            <div class="metric-label">Words</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{metrics.hashtag_count}</div>
                            <div class="metric-label">Hashtags</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Engagement score
                        score_color = "#28a745" if metrics.engagement_score >= 7 else "#ffc107" if metrics.engagement_score >= 4 else "#dc3545"
                        st.markdown(f"""
                        <div class="engagement-score" style="background: {score_color};">
                            Engagement Score: {metrics.engagement_score:.1f}/10
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.write(f"**Readability:** {metrics.readability_score}")
                        
                        # Recommendations
                        with st.expander("💡 Optimization Tips"):
                            recommendations = []
                            if metrics.character_count > 1300:
                                recommendations.append("Consider shortening for better engagement")
                            if metrics.hashtag_count == 0 and include_hashtags:
                                recommendations.append("Add hashtags to increase discoverability")
                            if metrics.engagement_score < 5:
                                recommendations.append("Add questions or call-to-actions to boost engagement")
                            if '?' not in edited_post:
                                recommendations.append("Consider adding a question to encourage comments")
                            
                            for rec in recommendations:
                                st.write(f"• {rec}")
                
                # Action buttons
                st.subheader("🎬 Actions")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    if st.button("📋 Copy Post", use_container_width=True):
                        st.code(edited_post, language=None)
                        st.success("Ready to copy!")
                
                with col2:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        st.session_state.generated_post = ""
                        st.rerun()
                
                with col3:
                    st.download_button(
                        label="💾 Download",
                        data=edited_post,
                        file_name=f"linkedin_post_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col4:
                    if st.button("✨ Enhance", use_container_width=True):
                        with st.spinner("Enhancing your post..."):
                            try:
                                enhance_prompt = f"""
                                Enhance this LinkedIn post to maximize engagement:
                                
                                {edited_post}
                                
                                Improvements to make:
                                - Stronger hook in the first line
                                - Better storytelling flow
                                - More compelling call-to-action
                                - Strategic emoji placement
                                - Improved readability
                                - Keep core message intact
                                """
                                
                                genai.configure(api_key=api_key)
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                enhanced_response = model.generate_content(enhance_prompt)
                                st.session_state.generated_post = enhanced_response.text
                                st.rerun()
                            except Exception as e:
                                st.error(f"Enhancement failed: {str(e)}")
                
                with col5:
                    if generate_image and st.button("🎨 Create Image", use_container_width=True):
                        with st.spinner("Creating post image..."):
                            try:
                                post_image = create_post_image(edited_post)
                                st.image(post_image, caption="Generated Post Image", use_container_width=True)
                                
                                # Convert to bytes for download
                                img_buffer = io.BytesIO()
                                post_image.save(img_buffer, format='PNG')
                                img_data = img_buffer.getvalue()
                                
                                st.download_button(
                                    label="📥 Download Image",
                                    data=img_data,
                                    file_name=f"linkedin_post_image_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.png",
                                    mime="image/png"
                                )
                            except Exception as e:
                                st.error(f"Image generation failed: {str(e)}")
        
        with tab2:
            # Analytics dashboard
            st.header("📊 Advanced Analytics Dashboard")
            
            if st.session_state.post_history:
                # Create analytics data
                analytics_df = pd.DataFrame([
                    {
                        'Date': post['timestamp'].date(),
                        'Template': post['template'],
                        'Characters': len(post['content']),
                        'Words': len(post['content'].split()),
                        'Hashtags': len(re.findall(r'#\w+', post['content'])),
                        'Engagement_Score': calculate_post_metrics(post['content']).engagement_score
                    }
                    for post in st.session_state.post_history
                ])
                
                # Overview metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{len(st.session_state.post_history)}</div>
                        <div class="metric-label">Posts Created</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    avg_engagement = analytics_df['Engagement_Score'].mean()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{avg_engagement:.1f}/10</div>
                        <div class="metric-label">Avg Engagement</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    most_used_template = analytics_df['Template'].mode()[0] if not analytics_df.empty else "N/A"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{most_used_template}</div>
                        <div class="metric-label">Top Template</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    avg_words = analytics_df['Words'].mean() if not analytics_df.empty else 0
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{int(avg_words)}</div>
                        <div class="metric-label">Avg Words</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # Charts section
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Engagement Over Time")
                    if not analytics_df.empty:
                        fig = px.line(
                            analytics_df, 
                            x='Date', 
                            y='Engagement_Score',
                            markers=True,
                            labels={'Engagement_Score': 'Engagement Score'},
                            color_discrete_sequence=['#0077b5']
                        )
                        fig.update_layout(
                            xaxis_title='Date',
                            yaxis_title='Score (0-10)',
                            yaxis_range=[0,10],
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No analytics data yet")
                
                with col2:
                    st.subheader("Template Performance")
                    if not analytics_df.empty:
                        template_df = analytics_df.groupby('Template')['Engagement_Score'].mean().reset_index()
                        fig = px.bar(
                            template_df,
                            x='Template',
                            y='Engagement_Score',
                            labels={'Engagement_Score': 'Avg Engagement Score'},
                            color='Engagement_Score',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(
                            xaxis_title='Template',
                            yaxis_title='Avg Score',
                            yaxis_range=[0,10],
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No template data yet")
                
                st.divider()
                
                # Detailed metrics
                st.subheader("Detailed Post Metrics")
                if not analytics_df.empty:
                    # Add calculated metrics
                    analytics_df['Readability'] = analytics_df.apply(
                        lambda row: calculate_post_metrics(
                            st.session_state.post_history[row.name]['content']
                        ).readability_score, 
                        axis=1
                    )
                    
                    # Display dataframe with formatting
                    st.dataframe(
                        analytics_df[['Date', 'Template', 'Words', 'Hashtags', 
                                    'Engagement_Score', 'Readability']]
                        .sort_values('Date', ascending=False)
                        .rename(columns={
                            'Date': 'Date',
                            'Template': 'Template',
                            'Words': 'Words',
                            'Hashtags': 'Hashtags',
                            'Engagement_Score': 'Engagement',
                            'Readability': 'Readability'
                        }),
                        use_container_width=True
                    )
                else:
                    st.info("Generate more posts to see detailed metrics")
            else:
                st.info("📝 Generate your first post to see analytics")
        
        with tab3:
            # Post history
            st.header("📚 Post History")
            
            if st.session_state.post_history:
                # Sort history by timestamp descending
                sorted_history = sorted(
                    st.session_state.post_history, 
                    key=lambda x: x['timestamp'], 
                    reverse=True
                )
                
                for idx, post in enumerate(sorted_history):
                    with st.expander(f"Post #{idx+1} - {post['template']} ({post['timestamp'].strftime('%Y-%m-%d %H:%M')})"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Template Used:** {post['template']}")
                            st.text_area(
                                f"Content #{idx+1}", 
                                value=post['content'], 
                                height=200,
                                key=f"history_{idx}"
                            )
                        with col2:
                            metrics = calculate_post_metrics(post['content'])
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-value">{metrics.word_count}</div>
                                <div class="metric-label">Words</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-value">{metrics.engagement_score:.1f}/10</div>
                                <div class="metric-label">Engagement</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Action buttons
                        if st.button(f"✏️ Load into Editor", key=f"load_{idx}"):
                            st.session_state.generated_post = post['content']
                            st.session_state.current_template = post['template']
                            st.success("Post loaded into editor! Switch to Create tab.")
                        
                        if st.button(f"🗑️ Delete", key=f"delete_{idx}"):
                            del st.session_state.post_history[idx]
                            st.rerun()
            else:
                st.info("📭 Your post history is empty. Generate your first post!")
        
        with tab4:
            # Learning Hub
            st.header("🎓 LinkedIn Content Learning Hub")
            
            with st.expander("📝 LinkedIn Best Practices"):
                st.markdown("""
                **Crafting High-Performing LinkedIn Content:**
                
                - 💡 **Hook in First 3 Lines:** Capture attention immediately with a strong hook
                - 👥 **Add Value First:** Focus on audience needs before self-promotion
                - 🔢 **Use Formatting:** Short paragraphs (2-3 lines), bullet points, emojis
                - ❓ **Ask Questions:** Boost comments by ending with a question
                - 🏷️ **Strategic Hashtags:** Use 3-5 relevant hashtags (#Industry, #Topic)
                - 📸 **Visuals Matter:** Posts with images get 2x more engagement
                - ⏰ **Timing:** Best posting times: 8-10AM & 5-6PM (local time)
                """)
            
            with st.expander("🚀 Content Strategy Tips"):
                st.markdown("""
                **Effective Content Strategy Framework:**
                
                1. **Define Your Pillars (3-5 core topics):**
                   - Professional expertise
                   - Industry insights
                   - Personal development
                   - Company culture
                
                2. **Content Mix Balance:**
                   - 50% Educational/Insights
                   - 30% Industry News/Commentary
                   - 20% Personal/Behind-the-Scenes
                
                3. **Engagement Boosters:**
                   - Use "What do you think?" instead of "Thoughts?"
                   - Tag relevant people in comments
                   - Respond to all comments within 24 hours
                
                4. **Optimal Post Length:**
                   - 800-1,300 characters performs best
                   - Minimum 3 paragraphs for storytelling
                """)
            
            with st.expander("📊 Analytics Guide"):
                st.markdown("""
                **Understanding Engagement Metrics:**
                
                - 👍 **Engagement Rate Formula:**  
                  (Reactions + Comments + Shares) / Impressions × 100
                - 🎯 **Benchmarks:**
                  - Good: 2-5% engagement rate
                  - Excellent: 5%+ engagement rate
                
                **Improving Key Metrics:**
                
                | Metric       | How to Improve                     |
                |--------------|------------------------------------|
                | Impressions  | Post consistently (3-5x/week)      |
                | CTR          | Use compelling hooks & visuals     |
                | Comments     | End with open-ended questions      |
                | Shares       | Create unique insights/data        |
                
                **Algorithm Factors:**
                - Dwell time (how long people view your post)
                - Comment reply depth (responses to comments)
                - Profile completeness (photo, headline, about)
                """)
            
            with st.expander("🤖 AI Prompting Tips"):
                st.markdown("""
                **Getting Better Results from AI:**
                
                - 🎯 **Be Specific:**  
                  "Create a LinkedIn post about remote work productivity for tech managers focusing on meeting efficiency"
                
                - 📚 **Provide Context:**  
                  "I'm a senior developer with 10 years experience in fintech"
                
                - 🛠️ **Request Formatting:**  
                  "Use bullet points for key takeaways and include 3 emojis"
                
                - 🔄 **Iterate:**  
                  "Make this more inspirational" or "Shorten to under 800 characters"
                
                - 🧠 **Add Personality:**  
                  "Include a personal story about overcoming procrastination"
                """)
    else:
        st.warning("🔑 Please enter your API key in the sidebar to get started")

if __name__ == "__main__":
    main()
