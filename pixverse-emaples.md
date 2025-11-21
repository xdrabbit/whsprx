#pixverse text to video example
curl --location --request POST 'https://app-api.pixverse.ai/openapi/v2/video/text/generate' \
--header 'API-KEY: your-api-key' \
--header 'Ai-trace-id: {{$string.uuid}}' \
--header 'Content-Type: application/json' \
--data-raw '{
    "aspect_ratio": "16:9",
    "duration": 5,
    "model": "v5",
    //"motion_mode": "normal",
    "negative_prompt": "string",
    //"camera_movement": "zoom_in", //Use this field to apply camera movement if needed.
    "prompt": "string",
    "quality": "540p",
    "seed": 0,
    //"template_id": 302325299692608
}'

#response example
{
    "ErrCode": 0,
    "ErrMsg": "string",
    "Resp": {
        "video_id": 0
    }
}

#upload image
curl --location --request POST 'https://app-api.pixverse.ai/openapi/v2/image/upload' \
--header 'API-KEY: your-api-key' \
--header 'Ai-trace-id: {{$string.uuid}}' \
--form 'image=@""' \
--form 'image_url="https://media.pixverse.ai/openapi%2Ff4c512d1-0110-4360-8515-d84d788ca8d1test_image_auto.jpg"'

#reponse example
{
    "ErrCode": 0,
    "ErrMsg": "string",
    "Resp": {
        "img_id": 0,
        "img_url": "string"
    }
}

#image to video
curl --location --request POST 'https://app-api.pixverse.ai/openapi/v2/video/img/generate' \
--header 'API-KEY: your-api-key' \
--header 'Ai-trace-id: {{$string.uuid}}' \
--header 'Content-Type: application/json' \
--data-raw '{
    "duration": 5,
    "img_id": 0,
    "model": "v4.5",
    "motion_mode": "normal",
    "negative_prompt": "string",
    //"camera_movement": "zoom_in", //Use this field to apply camera movement if needed.
    "prompt": "string",
    "quality": "540p",
    //"template_id": 302325299692608, //Use this field to apply template which you activated
    //"sound_effect_switch":true,
    //"sound_effect_content":"",
    //"lip_sync_tts_switch":true,
    //"lip_sync_tts_content":"",
    //"lip_sync_tts_speaker_id":"",
    "seed": 0
}'

#get video generation status
curl --location --request GET 'https://app-api.pixverse.ai/openapi/v2/video/result/' \
--header 'API-KEY: your-api-key' \
--header 'Ai-trace-id: {{$string.uuid}}'

#response example
{
    "ErrCode": 0,
    "ErrMsg": "string",
    "Resp": {
        "create_time": "string",
        "id": 0,
        "modify_time": "string",
        "negative_prompt": "string",
        "outputHeight": 0,
        "outputWidth": 0,
        "prompt": "string",
        "resolution_ratio": 0,
        "seed": 0,
        "size": 0,
        "status": 0,
        "style": "string",
        "url": "string"
    }
}