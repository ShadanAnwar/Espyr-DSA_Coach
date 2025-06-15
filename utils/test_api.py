import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_groq_api():
    try:
        # Initialize Groq client
        client = Groq(api_key=("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"))
        
        # Test a simple completion
        response = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": "Just say 'API is working'"
            }],
            model="llama3-70b-8192",  # or your preferred model
            temperature=0.5,
            max_tokens=20
        )
        
        # Print the response
        print("✅ API Response:")
        print(response.choices[0].message.content)
        
        return True
        
    except Exception as e:
        print("❌ API Error:")
        print(str(e))
        return False

if __name__ == "__main__":
    print("Testing Groq API connection...")
    if test_groq_api():
        print("🎉 Groq API is working properly!")
    else:
        print("🔴 Groq API connection failed")