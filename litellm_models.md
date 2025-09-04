# LiteLLM Configured Models

## Overview
This document lists all models currently configured in the LiteLLM server for use with Open WebUI.

**LiteLLM Server**: http://localhost:4001  
**Configuration File**: `/Users/cosburn/open_webui/litellm_config.yaml`  
**Last Updated**: 2025-08-17

## Configured Models

### Local Models (LM Studio)

#### gpt-oss-20b
- **Model Name**: `gpt-oss-20b`
- **Provider**: Local LM Studio
- **LiteLLM Model ID**: `openai/gpt-oss-20b`
- **API Base**: `http://127.0.0.1:1234/v1`
- **Status**: ✅ Active
- **Description**: GPT-OSS 20B model running locally in LM Studio
- **File**: `gpt-oss-20b-MXFP4.gguf`
- **Quantization**: MXFP4
- **Size**: 12.11 GB
- **Tool Use**: Supported

### OpenAI Models (Top 7 Selection)

#### gpt-5 (Flagship)
- **Model Name**: `gpt-5`
- **Provider**: OpenAI
- **Context Window**: 400,000 tokens
- **Status**: ✅ Active
- **Best For**: Complex reasoning, coding, multimodal tasks
- **Performance**: 94.6% AIME math, 74.9% SWE-bench coding
- **Features**: Multimodal (text, vision, audio), adjustable reasoning depth

#### gpt-5-mini (Cost-Effective Flagship)
- **Model Name**: `gpt-5-mini`
- **Provider**: OpenAI
- **Context Window**: 400,000 tokens
- **Status**: ✅ Active
- **Best For**: General purpose tasks with cost efficiency
- **Features**: Multimodal (text, vision, audio)

#### o3 (Reasoning Specialist)
- **Model Name**: `o3`
- **Provider**: OpenAI
- **Status**: ✅ Active
- **Best For**: Deep reasoning, math, logic, complex analysis
- **Features**: Multi-step problem solving, research-grade reasoning

#### gpt-4o (Multimodal Workhorse)
- **Model Name**: `gpt-4o`
- **Provider**: OpenAI
- **Status**: ✅ Active
- **Best For**: General chat, multimodal tasks
- **Features**: Text, vision, audio capabilities

#### gpt-4.1 (Advanced Instructions)
- **Model Name**: `gpt-4.1`
- **Provider**: OpenAI
- **Status**: ✅ Active
- **Best For**: Improved instruction-following, long-context understanding
- **Features**: Enhanced context handling

#### gpt-4o-search-preview (Real-time Info)
- **Model Name**: `gpt-4o-search-preview`
- **Provider**: OpenAI
- **Status**: ✅ Active
- **Best For**: Current information retrieval, web search
- **Features**: Real-time web access

#### o1 (Alternative Reasoning)
- **Model Name**: `o1`
- **Provider**: OpenAI
- **Status**: ✅ Active
- **Best For**: Reasoning tasks, alternative to o3
- **Features**: Problem-solving focused

### Anthropic Models (Top 6 Selection - Verified Available)

#### claude-opus-4-1-20250805 (Claude 4.1 Opus - Flagship)
- **Model Name**: `claude-opus-4-1-20250805`
- **Provider**: Anthropic
- **Context Window**: 200,000 tokens
- **Status**: ✅ Active
- **Best For**: Complex coding, advanced reasoning, multi-step workflows
- **Performance**: 74.5% SWE-bench Verified
- **Features**: Extended thinking with tool use, vision capabilities
- **Pricing**: $15/MTok input, $75/MTok output
- **Tier**: Flagship reasoning

#### claude-opus-4-20250514 (Claude 4 Opus - Fallback Flagship)
- **Model Name**: `claude-opus-4-20250514`
- **Provider**: Anthropic
- **Context Window**: 200,000 tokens
- **Status**: ✅ Active
- **Best For**: Complex agents, near-Opus 4.1 performance
- **Features**: Advanced reasoning, coding, vision, tool use
- **Pricing**: $15/MTok input, $75/MTok output
- **Tier**: Flagship fallback

#### claude-sonnet-4-20250514 (Claude 4 Sonnet - Balanced Default)
- **Model Name**: `claude-sonnet-4-20250514`
- **Provider**: Anthropic
- **Context Window**: 200,000 tokens (1M with beta header)
- **Max Output**: 64k tokens
- **Status**: ✅ Active
- **Best For**: Balanced performance, general tasks, cost-effective reasoning
- **Performance**: 72.7% SWE-bench
- **Features**: Hybrid near-instant and extended reasoning, vision
- **Pricing**: $3/MTok input, $15/MTok output
- **Tier**: Balanced default

#### claude-3-7-sonnet-20250219 (Claude 3.7 Sonnet - Budget Powerhouse)
- **Model Name**: `claude-3-7-sonnet-20250219`
- **Provider**: Anthropic
- **Context Window**: 200,000 tokens
- **Max Output**: 128k tokens (beta)
- **Status**: ✅ Active
- **Best For**: Large plans, test generation, bulk code comments
- **Features**: Extended thinking toggle, vision, coding
- **Pricing**: $3/MTok input, $15/MTok output
- **Tier**: Budget powerhouse

#### claude-3-5-haiku-20241022 (Claude 3.5 Haiku - Fast & Cost-Effective)
- **Model Name**: `claude-3-5-haiku-20241022`
- **Provider**: Anthropic
- **Context Window**: 200,000 tokens
- **Status**: ✅ Active
- **Best For**: Routing, classification, extraction, light transforms, agent tool calls
- **Features**: High throughput, low latency, vision
- **Pricing**: $0.8/MTok input, $4/MTok output
- **Tier**: Fast & cost-effective

#### claude-3-haiku-20240307 (Claude 3 Haiku - Legacy Fast)
- **Model Name**: `claude-3-haiku-20240307`
- **Provider**: Anthropic
- **Context Window**: 200,000 tokens
- **Status**: ✅ Active
- **Best For**: Legacy fast processing, basic text tasks
- **Features**: Fast text processing
- **Pricing**: $0.25/MTok input, $1.25/MTok output
- **Tier**: Legacy fast

### Google Gemini Models (Top 8 Selection)

#### gemini-2-5-pro (Gemini 2.5 Pro - Flagship)
- **Model Name**: `gemini-2-5-pro`
- **Provider**: Google Gemini
- **Context Window**: 1,048,576 tokens (1M)
- **Max Output**: 65,536 tokens
- **Status**: ✅ Active
- **Best For**: Complex reasoning, advanced coding, multimodal tasks
- **Features**: Text, vision, audio, coding, reasoning
- **Tier**: Flagship

#### gemini-2-5-flash (Gemini 2.5 Flash - Balanced Flagship)
- **Model Name**: `gemini-2-5-flash`
- **Provider**: Google Gemini
- **Context Window**: 1,048,576 tokens (1M)
- **Max Output**: 65,536 tokens
- **Status**: ✅ Active
- **Best For**: Balanced performance, general tasks, fast responses
- **Features**: Text, vision, coding, fast reasoning
- **Tier**: Balanced flagship

#### gemini-2-0-flash-001 (Gemini 2.0 Flash - Current Gen)
- **Model Name**: `gemini-2-0-flash-001`
- **Provider**: Google Gemini
- **Context Window**: 1,048,576 tokens (1M)
- **Max Output**: 8,192 tokens
- **Status**: ✅ Active
- **Best For**: Fast and versatile multimodal tasks
- **Features**: Text, vision, audio, coding
- **Tier**: Current generation

#### gemini-1-5-pro-002 (Gemini 1.5 Pro - Ultra-Long Context)
- **Model Name**: `gemini-1-5-pro-002`
- **Provider**: Google Gemini
- **Context Window**: 2,000,000 tokens (2M)
- **Max Output**: 8,192 tokens
- **Status**: ✅ Active
- **Best For**: Very long context tasks, document analysis
- **Features**: Text, vision, coding, ultra-long context
- **Tier**: Long context specialist

#### gemini-1-5-flash-002 (Gemini 1.5 Flash - Fast Reliable)
- **Model Name**: `gemini-1-5-flash-002`
- **Provider**: Google Gemini
- **Context Window**: 1,000,000 tokens (1M)
- **Max Output**: 8,192 tokens
- **Status**: ✅ Active
- **Best For**: Fast general purpose tasks
- **Features**: Text, vision, coding
- **Tier**: Fast & reliable

#### gemini-1-5-flash-8b (Gemini 1.5 Flash-8B - Cost Effective)
- **Model Name**: `gemini-1-5-flash-8b`
- **Provider**: Google Gemini
- **Context Window**: 1,000,000 tokens (1M)
- **Max Output**: 8,192 tokens
- **Status**: ✅ Active
- **Best For**: High throughput, cost-effective tasks
- **Features**: Text, vision, fast processing
- **Tier**: Most cost-effective

#### gemini-2-0-flash-thinking-exp (Gemini 2.0 Flash Thinking - Experimental)
- **Model Name**: `gemini-2-0-flash-thinking-exp`
- **Provider**: Google Gemini
- **Context Window**: 1,048,576 tokens (1M)
- **Max Output**: 65,536 tokens
- **Status**: ✅ Active
- **Best For**: Complex reasoning with visible thought process
- **Features**: Text, vision, thinking mode, reasoning
- **Tier**: Thinking experimental

#### gemini-2-0-flash-exp-image-generation (Gemini 2.0 Flash Image Generation - Experimental)
- **Model Name**: `gemini-2-0-flash-exp-image-generation`
- **Provider**: Google Gemini
- **Context Window**: 1,048,576 tokens (1M)
- **Max Output**: 8,192 tokens
- **Status**: ✅ Active
- **Best For**: Image generation and visual content creation
- **Features**: Text, vision, image generation
- **Tier**: Image generation experimental

#### gemini-2-5-flash-lite (Gemini 2.5 Flash-Lite - Ultra Cost-Effective Chat)
- **Model Name**: `gemini-2-5-flash-lite`
- **Provider**: Google Gemini
- **Context Window**: 1,048,576 tokens (1M)
- **Max Output**: 65,536 tokens
- **Status**: ✅ Active
- **Best For**: High-volume chat, routing, classification, light tasks
- **Features**: Text, vision, chat completion, high throughput
- **Pricing**: $0.10/MTok input, $0.40/MTok output
- **Tier**: Ultra cost-effective chat

## Configuration Details

### LiteLLM Settings
- **Master Key**: `litellm-master-key-2024`
- **Load Balancing**: Enabled
- **Fallbacks**: Enabled

### Connection Setup
**Open WebUI Connection:**
- Connection Type: OpenAI API
- API Base URL: `http://localhost:4001/v1`
- API Key: `litellm-master-key-2024`
- Name: LiteLLM Direct

## Notes
- Currently using direct connection approach (recommended)
- LiteLLM pipeline available but using direct connection for reliability
- Environment variables stored in `/Users/cosburn/open_webui/.env.litellm`
- All API keys for cloud providers configured but only local model active