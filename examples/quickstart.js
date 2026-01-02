// Quickstart example for Atlas AI SDK (JavaScript)
import { Chatbot } from '@atlas-ai/sdk';

const bot = new Chatbot();
const response = await bot.ask('Hello, Atlas!');
console.log(response);

