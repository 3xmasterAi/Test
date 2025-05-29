import streamlit as st
import google.generativeai as genai
import requests
from PIL import Image
import io
import base64
import json
import time

# Page configuration
st.set_page_config(
    page_title="LinkedIn Post Generator",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #0077b5, #00a0dc);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .post-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #0077b5;
        margin: 1rem 0;
    }
    .stButton > button {
        background: linear-gradient(90deg, #0077b5, #00a0dc);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #005885, #0077b5);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🚀 LinkedIn Post Generator</h1>
    <p>Create engaging LinkedIn posts with AI-generated content and images - Powered by Google AI Studio</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # API Key input
    api_key = st.text_input(
        "Google AI Studio API Key", 
        type="password",
        help="Get your free API key from https://aistudio.google.com/app/apikey"
    )
    
    if not api_key:
        st.warning("⚠️ Please enter your Google AI Studio API key to continue")
        st.info("""
        **How to get your free API key:**
        1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
        2. Sign in with your Google account
        3. Click 'Create API Key'
        4. Copy and paste it here
        
        **Free Tier Limits:**
        - 15 requests per minute
        - 1,500 requests per day
        - 1 million tokens per minute
        """)
    
    st.divider()
    
    # Post customization options
    st.header("📝 Post Options")
    
    post_tone = st.selectbox(
        "Post Tone",
        ["Professional", "Casual", "Inspirational", "Educational", "Humorous", "Thought-provoking"]
    )
    
    post_length = st.selectbox(
        "Post Length",
        ["Short (1-2 paragraphs)", "Medium (3-4 paragraphs)", "Long (5+ paragraphs)"]
    )
    
    include_hashtags = st.checkbox("Include Hashtags", value=True)
    include_cta = st.checkbox("Include Call-to-Action", value=True)
    generate_image = st.checkbox("Generate Accompanying Image", value=True)

# Main content area
if api_key:
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Initialize session state
    if 'generated_post' not in st.session_state:
        st.session_state.generated_post = ""
    if 'generated_image' not in st.session_state:
        st.session_state.generated_image = None
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💡 What's your post about?")
        
        # Topic input methods
        input_method = st.radio(
            "Choose input method:",
            ["Topic/Idea", "Key Points", "Article Summary"]
        )
        
        if input_method == "Topic/Idea":
            topic = st.text_input(
                "Enter your topic or main idea:",
                placeholder="e.g., Remote work productivity tips, Career growth strategies, Industry insights..."
            )
            additional_context = st.text_area(
                "Additional context (optional):",
                placeholder="Any specific points you want to include or your perspective on the topic..."
            )
            
        elif input_method == "Key Points":
            key_points = st.text_area(
                "Enter key points (one per line):",
                placeholder="• First important point\n• Second key insight\n• Third takeaway\n• Conclusion or action item"
            )
            
        else:  # Article Summary
            article_url = st.text_input("Article URL (optional):")
            article_summary = st.text_area(
                "Article summary or key insights:",
                placeholder="Summarize the main points of the article you want to discuss..."
            )
        
        # Generate button
        if st.button("🚀 Generate LinkedIn Post", key="generate_btn"):
            if ((input_method == "Topic/Idea" and topic) or 
                (input_method == "Key Points" and key_points) or 
                (input_method == "Article Summary" and article_summary)):
                
                with st.spinner("🤖 AI is crafting your LinkedIn post..."):
                    try:
                        # Prepare the prompt based on input method
                        if input_method == "Topic/Idea":
                            base_prompt = f"Topic: {topic}"
                            if additional_context:
                                base_prompt += f"\nContext: {additional_context}"
                        elif input_method == "Key Points":
                            base_prompt = f"Key points to cover:\n{key_points}"
                        else:
                            base_prompt = f"Article insights: {article_summary}"
                            if article_url:
                                base_prompt += f"\nSource: {article_url}"
                        
                        # Create comprehensive prompt for content generation
                        content_prompt = f"""
                        Create an engaging LinkedIn post based on the following:
                        
                        {base_prompt}
                        
                        Requirements:
                        - Tone: {post_tone}
                        - Length: {post_length}
                        - Target audience: LinkedIn professionals
                        - Make it engaging and valuable
                        - Use line breaks for readability
                        - Start with a hook to grab attention
                        {'- Include 5-8 relevant hashtags at the end' if include_hashtags else '- Do not include hashtags'}
                        {'- Include a clear call-to-action' if include_cta else '- Do not include call-to-action'}
                        
                        Format the post to be ready for LinkedIn posting.
                        """
                        
                        # Generate content using Gemini
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(content_prompt)
                        st.session_state.generated_post = response.text
                        
                        # Generate image if requested
                        if generate_image:
                            with st.spinner("🎨 Creating accompanying image..."):
                                # Create image prompt
                                image_prompt = f"""
                                Create a professional, clean, and modern image for a LinkedIn post about: {topic if input_method == 'Topic/Idea' else 'professional development'}. 
                                Style: Professional, clean, modern, suitable for LinkedIn
                                Colors: Use LinkedIn brand colors (blue tones) or professional color palette
                                Include: Subtle geometric shapes, clean typography space, professional aesthetic
                                Avoid: Cluttered design, too much text, unprofessional elements
                                """
                                
                                try:
                                    # Using Gemini's image generation capability
                                    image_model = genai.GenerativeModel('gemini-1.5-pro')
                                    image_response = image_model.generate_content([
                                        f"Generate a professional LinkedIn post image: {image_prompt}",
                                        "Make it visually appealing and professional"
                                    ])
                                    
                                    # Note: Gemini doesn't directly generate images, so we'll create a placeholder
                                    # In a real implementation, you'd use DALL-E, Midjourney API, or similar
                                    st.info("📸 Image generation placeholder - integrate with your preferred image generation service")
                                    
                                except Exception as e:
                                    st.warning(f"Image generation not available: {str(e)}")
                        
                        st.success("✅ Post generated successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating post: {str(e)}")
                        st.info("💡 Make sure your API key is valid and you haven't exceeded rate limits.")
            else:
                st.warning("⚠️ Please provide the required input based on your selected method.")
    
    with col2:
        st.header("📊 Quick Stats")
        
        # API usage info
        st.info("""
        **Free Tier Usage:**
        - ✅ 15 requests/minute
        - ✅ 1,500 requests/day  
        - ✅ Completely free
        """)
        
        # Tips
        st.header("💡 Pro Tips")
        st.markdown("""
        **For better results:**
        - Be specific about your topic
        - Mention target audience
        - Add personal insights
        - Keep it relevant to your industry
        - Use trending topics when appropriate
        """)
        
        # Post templates
        with st.expander("📋 Popular Post Templates"):
            st.markdown("""
            **Industry Insight:**
            "Here's what I learned about [topic]..."
            
            **Personal Experience:**
            "Yesterday, something happened that changed my perspective..."
            
            **Tips/Advice:**
            "5 things I wish I knew when starting my career..."
            
            **Question/Discussion:**
            "What's your take on [current trend]?"
            """)

    # Display generated content
    if st.session_state.generated_post:
        st.divider()
        st.header("📝 Generated LinkedIn Post")
        
        # Post preview
        st.markdown("""
        <div class="post-container">
        """, unsafe_allow_html=True)
        
        # Character count
        char_count = len(st.session_state.generated_post)
        st.caption(f"Character count: {char_count} {'(Good for LinkedIn)' if char_count <= 3000 else '(Consider shortening)'}")
        
        # Editable post content
        edited_post = st.text_area(
            "Edit your post:",
            value=st.session_state.generated_post,
            height=300,
            key="post_editor"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Copy to Clipboard"):
                st.code(edited_post, language=None)
                st.success("Post ready to copy!")
        
        with col2:
            if st.button("🔄 Regenerate"):
                st.session_state.generated_post = ""
                st.rerun()
        
        with col3:
            # Download as text file
            st.download_button(
                label="💾 Download Post",
                data=edited_post,
                file_name="linkedin_post.txt",
                mime="text/plain"
            )
        
        with col4:
            if st.button("✨ Enhance Post"):
                with st.spinner("Enhancing your post..."):
                    try:
                        enhance_prompt = f"""
                        Enhance this LinkedIn post to make it more engaging:
                        
                        {edited_post}
                        
                        Improvements to make:
                        - Add more compelling hooks
                        - Improve readability
                        - Make it more actionable
                        - Keep the same core message
                        - Maintain professional tone
                        """
                        
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        enhanced_response = model.generate_content(enhance_prompt)
                        st.session_state.generated_post = enhanced_response.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error enhancing post: {str(e)}")

    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p>💼 <strong>LinkedIn Post Generator</strong> - Powered by Google AI Studio</p>
        <p>Made with ❤️ using Streamlit | Free to use with Google's generous API limits</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Welcome screen when no API key
    st.markdown("""
    ## 🚀 Welcome to LinkedIn Post Generator!
    
    This tool helps you create engaging LinkedIn posts using Google's AI technology - completely free!
    
    ### ✨ Features:
    - 🤖 AI-powered content generation
    - 🎨 Professional image suggestions  
    - 📊 Multiple post formats and tones
    - 💡 Built-in templates and tips
    - 📱 Ready-to-post formatting
    - 💰 **Completely FREE** with Google AI Studio
    
    ### 🔑 Getting Started:
    1. Get your free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
    2. Enter it in the sidebar
    3. Start generating amazing LinkedIn content!
    
    ### 💼 Perfect for:
    - Professionals looking to build their brand
    - Content creators and marketers
    - Job seekers wanting to increase visibility
    - Anyone wanting to share insights on LinkedIn
    """)
    
    # Quick demo section
    with st.expander("👀 See Example Output"):
        st.markdown("""
        **Sample Input:** "Tips for remote work productivity"
        
        **Generated Post:**
        
        🏠 Working remotely for 3+ years taught me that productivity isn't about working MORE hours—it's about working SMARTER.
        
        Here are 5 game-changing strategies that transformed my remote work experience:
        
        🎯 **Time-blocking over multitasking**
        Instead of juggling 10 tasks, I block specific hours for deep work. Result? 40% more productive output.
        
        📱 **Digital boundaries are non-negotiable**  
        Slack notifications off after 6 PM. Email checks limited to 3x daily. My mental health thanked me.
        
        🌱 **Micro-breaks = macro results**
        5-minute walks every hour keep my energy steady. Sounds simple, but it's revolutionary.
        
        What's your #1 remote work hack? Drop it below! 👇
        
        #RemoteWork #Productivity #WorkFromHome #ProfessionalDevelopment #WorkLifeBalance
        """)
