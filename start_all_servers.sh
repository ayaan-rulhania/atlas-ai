#!/bin/bash
cd /Users/arulhania/Coding/atlas-ai

# Activate virtual environment
source .venv/bin/activate

# Start Chatbot Server (Port 5000)
cd apps/chatbot
python3 app.py > ../../data/logs/chatbot.log 2>&1 &
CHATBOT_PID=$!
echo "Chatbot Server started (PID: $CHATBOT_PID) - http://localhost:5000"

# Start Thor Result Setter Server (Port 5004)
python3 thor_result_setter_server.py > ../../data/logs/thor_result_setter.log 2>&1 &
THOR_PID=$!
echo "Thor Result Setter started (PID: $THOR_PID) - http://localhost:5004"

echo ""
echo "🚀 Atlas AI servers started successfully!"
echo "📱 Main Chat Interface: http://localhost:5000"
echo "⚙️  Result Setter: http://localhost:5004"
echo ""
echo "💡 Using combined Qwen3-4B + Thor 1.1 model"
echo ""
echo "To stop all servers: kill $CHATBOT_PID $THOR_PID"
echo "Or run: pkill -f 'python3 app.py' && pkill -f 'thor_result_setter_server.py'"