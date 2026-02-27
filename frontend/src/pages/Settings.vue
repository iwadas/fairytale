<template>

    <div class="flex flex-col gap-10">
        <section class="container-background container mx-auto rounded-[10px] text-light p-6">
            <h2 class="text-lg mb-6">
                <font-awesome-icon icon="volume-up" class="mr-2"></font-awesome-icon>
                TTS
            </h2>
            <div class="flex flex-col gap-4 text-xs">
                <form-input 
                    :label="'TTS Provider'"
                    :type="'select'"
                    :options="TTS_PROVIDERS"
                    v-model="selectedOptions.selected_tts_provider"
                />
    
                <div v-for="option in TTS_PROVIDER_OPTIONS[selectedOptions.selected_tts_provider]" :key="option.name">
                    <form-input 
                        :label="option.label"
                        :type="option.type"
                        v-model="selectedOptions.tts_provider_settings[selectedOptions.selected_tts_provider][option.name]"
                        :options="option.options"
                        :placeholder="option.placeholder"
                        :optional="option.optional"
                        :helper="option.helper"
                    />
                </div>

                <form-button
                    label="Save TTS Settings"
                    button_style="primary"
                    @clicked="saveSettings('tts')"
                    class="w-1/4 mx-auto"
                />
            </div>
        </section>
        <section class="container-background container mx-auto rounded-[10px] text-light p-6 ">
            <h2 class="text-lg mb-6">
                <font-awesome-icon icon="video" class="mr-2"></font-awesome-icon>
                VIDEO DIFFUSION
            </h2>
            <div class="flex flex-col gap-4 text-xs">
                <form-input 
                    :label="'Video Diffusion Provider'"
                    :type="'select'"
                    :options="DIFFUSION_PROVIDERS"
                    v-model="selectedOptions.selected_diffusion_provider"
                />
    
                <div v-for="option in DIFFUSION_PROVIDER_OPTIONS[selectedOptions.selected_diffusion_provider]" :key="option.name">
                    <form-input 
                        :label="option.label"
                        :type="option.type"
                        v-model="selectedOptions.diffusion_provider_settings[selectedOptions.selected_diffusion_provider][option.name]"
                        :options="option.options"
                        :placeholder="option.placeholder"
                        :optional="option.optional"
                        :helper="option.helper"
                    />
                </div>

                <form-button
                    label="Save Diffusion Settings"
                    button_style="primary"
                    @clicked="saveSettings('diffusion')"
                    class="w-1/4 mx-auto"
                />
            </div>
        </section>
        <section class="container-background container mx-auto rounded-[10px] text-light p-6 ">
            <h2 class="text-lg mb-6">
                <font-awesome-icon icon="robot" class="mr-2"></font-awesome-icon>
                LLM
            </h2>
            <div class="flex flex-col gap-4 text-xs">
                <form-input 
                    :label="'LLM Provider'"
                    type="select"
                    :options="LLM_PROVIDERS"
                    v-model="selectedOptions.selected_llm_provider"
                />
    
                <div v-for="option in LLM_PROVIDER_OPTIONS[selectedOptions.selected_llm_provider]" :key="option.name">
                    <form-input 
                        :label="option.label"
                        :type="option.type"
                        v-model="selectedOptions.llm_provider_settings[selectedOptions.selected_llm_provider][option.name]"
                        :options="option.options"
                        :placeholder="option.placeholder"
                        :optional="option.optional"
                        :helper="option.helper"
                    />
                </div>
                <form-button
                    label="Save LLM Settings"
                    button_style="primary"
                    @clicked="saveSettings('llm')"
                    class="w-1/4 mx-auto"
                />
            </div>
        </section>
    </div>



</template>


<script setup>

    import FormInput from '@/components/FormInput.vue'
    import FormButton from '@/components/FormButton.vue'
    import { onMounted, ref, reactive } from 'vue';
    import axios from 'axios'

    const selectedOptions = reactive({
        selected_tts_provider: 'gemini',
        selected_diffusion_provider: 'runware',
        selected_llm_provider: 'xai',
        tts_provider_settings: {
            gemini: {
                api_key: '',
                voice_name: 'zephyr',
                voice_style: '',
            },
            camb: {
                api_key: '',
                voice_model_id: '',
                language: 'english',
            }
        },
        diffusion_provider_settings: {
            runware: {
                api_key: '',
                diffusion_model: '',
                image_resolution: '1080x1080',
                fps: '24',
            }
        },
        llm_provider_settings: {
            xai: {
                api_key: '',
                ai_model: 'grok-4-1-fast-reasoning',
            },
            openai: {
                api_key: '',
                ai_model: 'gpt-4o-nano',
            },
            genai: {
                api_key: '',
            }
        }
    })

    const TTS_PROVIDERS = [
        {
            label: "Gemini",
            value: "gemini"
        },
        {
            label: "Camb.ai",
            value: "camb"
        }
    ]

    const TTS_PROVIDER_OPTIONS = {
        "gemini": [
            {
                label: "Api Key",
                name: "api_key",
                type: "text",
                optional: false,
                placeholder: "AI4SayB_NcwTN_Cnj11ldEQjrRbQWR0fV9wttK8"
            },
            {
                helper: "Check Voices and Styles on <a href='https://aistudio.google.com/generate-speech' target='_blank'>Google AI Studio</a>",
                label: "Voice Name",
                name: "voice_name",
                type: "select",
                options: [
                    // Zephyr, Puck, Charon, Kore, Fenrir, Leda, Orus, Aoede, Callirrhoe, Autonoe, Enceladus, Iapetus, Umbriel, Algieba, Despina, Erinome, Algenib, Raselgethi, Laomedeia, Achernar, Alnilam, Sheder, Gacrux, Pulcherrima, Archid, Zubenelgenubi, Vindemiatrix, Sadachbia, Sadaltager, Sufalt
                    {
                        label: "Zephyr",
                        value: "zephyr"
                    },
                    {
                        label: "Puck",
                        value: "puck"
                    },
                    {
                        label: "Charon",
                        value: "charon"
                    },
                    {
                        label: "Kore",
                        value: "kore"
                    },
                    {
                        label: "Fenrir",
                        value: "fenrir"
                    },
                    {
                        label: "Leda",
                        value: "leda"
                    },
                    {
                        label: "Orus",
                        value: "orus"
                    },
                    {
                        label: "Aoede",
                        value: "aoede"
                    },
                    {
                        label: "Callirrhoe",
                        value: "callirrhoe"
                    },
                    {
                        label: "Autonoe",
                        value: "autonoe"
                    },
                    {
                        label: "Enceladus",
                        value: "enceladus"
                    },
                    {
                        label: "Iapetus",
                        value: "iapetus"
                    },
                    {
                        label: "Umbriel",
                        value: "umbriel"
                    },
                    {
                        label: "Algieba",
                        value: "algieba"
                    },
                    {
                        label: "Despina",
                        value: "despina"
                    },
                    {
                        label: "Erinome",
                        value: "erinome"
                    },
                    {
                        label: "Algenib",
                        value: "algenib"
                    },
                    {
                        label: "Raselgethi",
                        value: "raselgethi"
                    },
                    {
                        label: "Laomedeia",
                        value: "laomedeia"
                    },
                    {
                        label: "Achernar",
                        value: "achernar"
                    },
                    {
                        label: "Alnilam",
                        value: "alnilam"
                    },
                    {
                        label: "Sheder",
                        value: "sheder"
                    },
                    {
                        label: "Gacrux",
                        value: "gacrux"
                    },
                    {
                        label: "Pulcherrima",
                        value: "pulcherrima"
                    },
                    {
                        label: "Archid",
                        value: "archid"
                    },
                    {
                        label: "Zubenelgenubi",
                        value: "zubenelgenubi"
                    },
                    {
                        label: "Vindemiatrix",
                        value: "vindemiatrix"
                    },
                    {
                        label: "Sadachbia",
                        value: "sadachbia"
                    },
                    {
                        label: "Sadaltager",
                        value: "sadaltager"
                    },
                    {
                        label: "Sufalt",
                        value: "sufalt"
                    }
                ]
            },
            {
                label: "Voice Style",
                name: "voice_style",
                type: "textarea",
                optional: true,
                placeholder: "Describe the voice style (e.g., \"Read aloud in a warm and friendly tone:\")"
            }
        ],
        "camb": [
            {
                label: "Api Key",
                name: "api_key",
                type: "text",
                optional: false,
                placeholder: "12d8eb48-ad15-414f-17a0-8bb913f412cd5",
            },
            {
                helper: "Check Voice Models or Create Your Own on <a href='https://studio.camb.ai/voice-library' target='_blank'>CAMB.AI</a>",
                label: "Voice Model ID",
                name: "voice_model_id",
                type: "text",
                optional: false,
                placeholder: "21m00Tcm4TlvDq8ikWAM"
            },
            {
                label: "Language",
                name: "language",
                type: "select",
                optional: true,
                options: [
                    {
                        label: "English",
                        value: "english"
                    },
                    {
                        label: "Spanish",
                        value: "spanish"
                    },
                    {
                        label: "French",
                        value: "french"
                    },
                    {
                        label: "German",
                        value: "german"
                    },
                    {
                        label: "Chinese",
                        value: "chinese"
                    },
                    {
                        label: "Japanese",
                        value: "japanese"
                    },
                    {
                        label: "Korean",
                        value: "korean"
                    },
                    {
                        label: "Italian",
                        value: "italian"
                    },
                    {
                        label: "Portuguese",
                        value: "portuguese"
                    }
                ]
            }
        ]
    }
    
    const DIFFUSION_PROVIDERS = [
        {
            label: "Runware",
            value: "runware"
        }
    ]

    const DIFFUSION_PROVIDER_OPTIONS = {
        "runware": [
            {
                label: "Api Key",
                name: "api_key",
                type: "text",
                optional: false,
                placeholder: "p1933ivUAIDzcj04bIdsanDrbqF7fBD1lCc"
            },
            {

                label: "Diffusion Model",
                name: "diffusion_model",
                type: "text",
                optional: false,
                helper: "Check <a href='https://runware.ai/pricing' target='_blank'>Runware Pricing</a> for available models, their capabilities and costs.",
                placeholder: "bytedance:1@1"
            },
            {
                label: "Image Resolution",
                name: "image_resolution",
                type: "select",
                optional: true,
                options: [
                    {
                        label: "512x512 (1:1)",
                        value: "512x512"
                    },
                    {
                        label: "768x768 (1:1)",
                        value: "768x768"
                    },
                    {
                        label: "1024x1024 (1:1)",
                        value: "1024x1024"
                    },
                    {
                        label: "1080x1080 (1:1)",
                        value: "1080x1080"
                    }
                ]
            },
            {
                label: "FPS",
                name: "fps",
                type: "select",
                optional: true,
                options: [
                    {
                        label: "24",
                        value: "24"
                    },
                    {
                        label: "30",
                        value: "30"
                    },
                    {
                        label: "60",
                        value: "60"
                    }
                ]
            }
        ]
    }

    const LLM_PROVIDERS = [
        {
            label: "OpenAI",
            value: "openai"
        },
        {
            label: "XAI",
            value: "xai"
        },
        {
            label: "Genai (NOT SUPPORTED YET)",
            value: "genai"
        },
    ]

    const LLM_PROVIDER_OPTIONS = {
        "openai": [
            {
                label: "Api Key",
                name: "api_key",
                type: "text",
                optional: false,
                placeholder: "sk-proj-**-**************************"
            },
            {
                label: "AI Model",
                name: "ai_model",
                type: "text",
                optional: false,
                placeholder: "gpt-4o-nano"
            }
        ],
        "xai": [
            {
                label: "Api Key",
                name: "api_key",
                type: "text",
                optional: false,
                placeholder: "xai-************************"
            },
            {
                label: "AI Model",
                name: "ai_model",
                type: "text",
                optional: false,
                placeholder: "grok-4-1-fast-reasoning"
            }
        ],
        "genai": [
            {
                label: "Api Key",
                name: "api_key",
                type: "text",
                optional: false,
                placeholder: "AIzaSyBUNcwTN_CnjZGldEQjrsVQWR0fb9wttK8"
            },
        ],
    }


    const saveSettings = async (category) => {
        try {

            const selected_provider = "selected_" + category + "_provider" 
            const provider_settings = category + "_provider_settings"

            const payload = {
                [selected_provider]: selectedOptions[selected_provider],
                [provider_settings]: selectedOptions[provider_settings][selectedOptions[selected_provider]]
            }

            console.log(`Saving ${category} settings:`, payload);
            await axios.put(`http://localhost:8000/settings`, payload);
            alert(`${category.toUpperCase()} settings saved successfully!`);

        } catch (error) {
            console.error(`Error saving ${category} settings:`, error);
            // alert(`Failed to save ${category.toUpperCase()} settings. Please try again.`);
        }
    }

    const fetchSettings = () => {
        axios.get('http://localhost:8000/settings')
            .then(res => {
                const data = res.data;
                console.log('Fetched settings:', data);

                if (!data) return;

                // Update selected providers
                selectedOptions.selected_tts_provider = data.selected_tts_provider || "gemini";
                selectedOptions.selected_diffusion_provider = data.selected_diffusion_provider || "runware";
                selectedOptions.selected_llm_provider = data.selected_llm_provider || "xai";

                if (data.tts_provider_settings){
                    const tts_provider_settings = data.tts_provider_settings;
                    selectedOptions.tts_provider_settings['gemini']['api_key'] = tts_provider_settings.gemini?.api_key || '';
                    selectedOptions.tts_provider_settings['gemini']['voice_name'] = tts_provider_settings.gemini?.voice_name || 'zephyr';
                    selectedOptions.tts_provider_settings['gemini']['voice_style'] = tts_provider_settings.gemini?.voice_style || '';
                    selectedOptions.tts_provider_settings['camb']['api_key'] = tts_provider_settings.camb?.api_key || '';
                    selectedOptions.tts_provider_settings['camb']['voice_model_id'] = tts_provider_settings.camb?.voice_model_id || '';
                    selectedOptions.tts_provider_settings['camb']['language'] = tts_provider_settings.camb?.language || 'english'; 
                }

                if (data.diffusion_provider_settings){
                    const diffusion_provider_settings = data.diffusion_provider_settings;
                    selectedOptions.diffusion_provider_settings['runware']['api_key'] = diffusion_provider_settings.runware?.api_key || '';
                    selectedOptions.diffusion_provider_settings['runware']['diffusion_model'] = diffusion_provider_settings.runware?.diffusion_model || '';
                    selectedOptions.diffusion_provider_settings['runware']['image_resolution'] = diffusion_provider_settings.runware?.image_resolution || '1080x1080';
                    selectedOptions.diffusion_provider_settings['runware']['fps'] = diffusion_provider_settings.runware?.fps || '24';
                }

                if (data.llm_provider_settings){
                    const llm_provider_settings = data.llm_provider_settings;
                    selectedOptions.llm_provider_settings['xai']['api_key'] = llm_provider_settings.xai?.api_key || '';
                    selectedOptions.llm_provider_settings['xai']['ai_model'] = llm_provider_settings.xai?.ai_model || 'grok-4-1-fast-reasoning';
                    selectedOptions.llm_provider_settings['openai']['api_key'] = llm_provider_settings.openai?.api_key || '';
                    selectedOptions.llm_provider_settings['openai']['ai_model'] = llm_provider_settings.openai?.ai_model || 'gpt-4o-nano';
                    selectedOptions.llm_provider_settings['genai']['api_key'] = llm_provider_settings.genai?.api_key || '';
                }
            })
            .catch(err => {
                console.error('Error fetching settings:', err);
            });
    }

    onMounted(()=>{
        fetchSettings();
    })



</script>