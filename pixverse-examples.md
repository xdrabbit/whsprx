# Upload Image

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/image/upload:
    post:
      summary: Upload Image
      deprecated: false
      description: >-
        Uploads an image to the server. 

        Image requirements

        1. maximum dimensions 4000*4000 pixels

        2. file size less than 20MB

        3. Supported formats: "png", "webp", "jpeg", "jpg" . supported mime-type
        "image/jpeg","image/jpg","image/png","image/webp"
      tags:
        - API Reference
        - OpenAPI 接口
      parameters:
        - name: API-KEY
          in: header
          description: api-key from PixVerse platform
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-trace-id
          in: header
          description: 'traceID format: UUID, must be unique for each request'
          required: true
          example: '{{$string.uuid}}'
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                image:
                  format: binary
                  type: string
                  description: Either image or image_url is required.
                  example: ''
                image_url:
                  description: >-
                    image file from url, application/octet-stream is not
                    supported.Either image or image_url is required. supported
                    mime-type "image/jpeg","image/jpg","image/png","image/webp"
                  example: >-
                    https://media.pixverse.ai/openapi%2Ff4c512d1-0110-4360-8515-d84d788ca8d1test_image_auto.jpg
                  type: string
            examples: {}
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                allOf:
                  - type: object
                    x-apidog-refs:
                      01JP7G4DBABJC41Q5GF009NQ58:
                        $ref: '#/components/schemas/controller.ResponseData'
                        x-apidog-overrides:
                          Resp: &ref_0
                            $ref: '#/components/schemas/dto.UploadImgResp'
                        required: []
                    x-apidog-orders:
                      - 01JP7G4DBABJC41Q5GF009NQ58
                    properties:
                      ErrCode:
                        type: integer
                      ErrMsg:
                        type: string
                      Resp: *ref_0
                    x-apidog-ignore-properties:
                      - ErrCode
                      - ErrMsg
                      - Resp
          headers: {}
          x-apidog-name: OK
        '500':
          description: 审核不通过
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/dto.ResponseData500'
          headers: {}
          x-apidog-name: Server Error
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-13016631-run
components:
  schemas:
    controller.ResponseData:
      type: object
      properties:
        ErrCode:
          type: integer
        ErrMsg:
          type: string
        Resp:
          $ref: '#/components/schemas/dto.V2OpenAPII2VResp'
      x-apidog-orders:
        - ErrCode
        - ErrMsg
        - Resp
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
    dto.V2OpenAPII2VResp:
      type: object
      properties:
        video_id:
          description: Video_id
          type: integer
      x-apidog-orders:
        - video_id
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
    dto.UploadImgResp:
      type: object
      properties:
        img_id:
          type: integer
        img_url:
          type: string
      x-apidog-orders:
        - img_id
        - img_url
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
    dto.ResponseData500:
      type: object
      properties:
        err_code:
          type: integer
          examples:
            - 500052
        err_msg:
          type: string
          examples:
            - 图片未过审，疑含敏感内容，请修改后重试。
        resp:
          type: string
      x-apidog-orders:
        - err_code
        - err_msg
        - resp
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```

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

# Text-to-Video generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/text/generate:
    post:
      summary: Text-to-Video generation
      deprecated: false
      description: Text-to-Video generation task
      tags:
        - API Reference
        - OpenAPI 接口
      parameters:
        - name: API-KEY
          in: header
          description: API-KEY from PixVerse platform
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-trace-id
          in: header
          description: 'traceID format: UUID, must be unique for each request'
          required: true
          example: '{{$string.uuid}}'
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                aspect_ratio:
                  description: Aspect ratio (16:9, 4:3, 1:1, 3:4, 9:16)
                  type: string
                  examples:
                    - '16:9'
                duration:
                  description: >-
                    Video duration (5, 8 seconds, --model=v3.5 only allows 5,8;
                    --quality=1080p does not support 8s)
                  type: integer
                  examples:
                    - 5
                model:
                  description: Model version (now supports v3.5/v4/v4.5/v5)
                  type: string
                  examples:
                    - v3.5
                motion_mode:
                  description: >-
                    Motion mode (normal, fast, --fast only available when
                    duration=5; --quality=1080p does not support fast) , not
                    supports on v5 
                  type: string
                  default: normal
                  examples:
                    - normal
                negative_prompt:
                  description: |
                    Negative prompt
                  type: string
                  maxLength: 2048
                prompt:
                  description: Prompt
                  type: string
                  maxLength: 2048
                quality:
                  description: Video quality ("360p"(Turbo model), "540p", "720p", "1080p")
                  type: string
                  examples:
                    - 540p
                seed:
                  description: 'Random seed, range: 0 - 2147483647'
                  type: integer
                style:
                  description: >-
                    Style (effective when model=v3.5, "anime", "3d_animation",
                    "clay", "comic", "cyberpunk") Do not include style parameter
                    unless needed
                  type: string
                  examples:
                    - anime
                template_id:
                  description: Template ID (template_id must be activated before use)
                  type: integer
                  examples:
                    - 302325299692608
                sound_effect_switch:
                  type: boolean
                sound_effect_content:
                  type: string
                lip_sync_switch:
                  type: boolean
                  description: >-
                    Set to true if you want to enable this feature. Default is
                    false.
                lip_sync_tts_content:
                  type: string
                  description: ~140 (UTF-8) characters
                lip_sync_tts_speaker_id:
                  type: string
                  description: 'id from Get speech tts list '
              x-apidog-refs: {}
              x-apidog-orders:
                - aspect_ratio
                - duration
                - model
                - motion_mode
                - negative_prompt
                - prompt
                - quality
                - seed
                - style
                - template_id
                - sound_effect_switch
                - sound_effect_content
                - lip_sync_switch
                - lip_sync_tts_content
                - lip_sync_tts_speaker_id
              required:
                - aspect_ratio
                - duration
                - model
                - prompt
                - quality
              x-apidog-ignore-properties: []
            example: |-
              {
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
              }
      responses:
        '200':
          description: Token Expired
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/controller.ResponseData'
          headers: {}
          x-apidog-name: OK
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-13016634-run
components:
  schemas:
    controller.ResponseData:
      type: object
      properties:
        ErrCode:
          type: integer
        ErrMsg:
          type: string
        Resp:
          $ref: '#/components/schemas/dto.V2OpenAPII2VResp'
      x-apidog-orders:
        - ErrCode
        - ErrMsg
        - Resp
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
    dto.V2OpenAPII2VResp:
      type: object
      properties:
        video_id:
          description: Video_id
          type: integer
      x-apidog-orders:
        - video_id
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

# Image-to-Video generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/img/generate:
    post:
      summary: Image-to-Video generation
      deprecated: false
      description: |
        Image-to-Video generation
      tags:
        - API Reference
        - OpenAPI 接口
      parameters:
        - name: API-KEY
          in: header
          description: API-KEY from PixVerse platform
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-trace-id
          in: header
          description: 'traceID format: UUID, must be unique for each request'
          required: true
          example: '{{$string.uuid}}'
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                duration:
                  description: >-
                    Video duration (5, 8 seconds, --model=v3.5 only allows 5,8;
                    --quality=1080p does not support 8s)
                  type: integer
                  examples:
                    - 5
                img_id:
                  type: integer
                  description: >-
                    Image ID from Upload image API. single image or single-image
                    templates
                  format: uint64
                img_ids:
                  type: array
                  items:
                    type: integer
                  description: >-
                    img_ids is only for multi-image templates. ex) "img_ids
                    ":[0,0]
                model:
                  description: |
                    Model version (now supports v3.5/v4/v4.5/v5)
                  type: string
                  examples:
                    - v3.5
                motion_mode:
                  description: >-
                    Motion mode (normal, fast, --fast only available when
                    duration=5; --quality=1080p does not support fast) , not
                    supports on v5 
                  type: string
                  default: normal
                  examples:
                    - normal
                negative_prompt:
                  description: Negative prompt
                  type: string
                  maxLength: 2048
                prompt:
                  description: Prompt
                  type: string
                  maxLength: 2048
                quality:
                  description: Video quality ("360p"(Turbo), "540p", "720p", "1080p")
                  type: string
                  examples:
                    - 540p
                seed:
                  description: 'Random seed, range: 0 - 2147483647'
                  type: integer
                style:
                  description: >-
                    Style (effective when model=v3.5, "anime", "3d_animation",
                    "clay", "comic", "cyberpunk") Do not include style parameter
                    unless needed
                  type: string
                  examples:
                    - anime
                template_id:
                  description: Template ID (template_id must be activated before use)
                  type: integer
                  examples:
                    - 302325299692608
                sound_effect_switch:
                  type: boolean
                  description: >-
                    Set to true if you want to enable this feature. Default is
                    false.
                sound_effect_content:
                  type: string
                  description: >-
                    Sound effect content to generate. If not provided, a sound
                    effect will be automatically generated based on the video
                    content.
                lip_sync_switch:
                  type: boolean
                  description: >-
                    Set to true if you want to enable this feature. Default is
                    false.
                lip_sync_tts_content:
                  type: string
                  description: >-
                    ~140 (UTF-8) characters. If the generated audio exceeds the
                    video duration, it will be truncated.
                lip_sync_tts_speaker_id:
                  type: string
                  description: 'id from Get speech tts list '
              x-apidog-refs: {}
              x-apidog-orders:
                - duration
                - img_id
                - img_ids
                - model
                - motion_mode
                - negative_prompt
                - prompt
                - quality
                - seed
                - style
                - template_id
                - sound_effect_switch
                - sound_effect_content
                - lip_sync_switch
                - lip_sync_tts_content
                - lip_sync_tts_speaker_id
              required:
                - duration
                - img_id
                - model
                - prompt
                - quality
              x-apidog-ignore-properties: []
            example: |-
              {
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
              }
      responses:
        '200':
          description: Token Expired
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/controller.ResponseData'
          headers: {}
          x-apidog-name: OK
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-13016633-run
components:
  schemas:
    controller.ResponseData:
      type: object
      properties:
        ErrCode:
          type: integer
        ErrMsg:
          type: string
        Resp:
          $ref: '#/components/schemas/dto.V2OpenAPII2VResp'
      x-apidog-orders:
        - ErrCode
        - ErrMsg
        - Resp
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
    dto.V2OpenAPII2VResp:
      type: object
      properties:
        video_id:
          description: Video_id
          type: integer
      x-apidog-orders:
        - video_id
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

# Transition(First-last frame) generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/transition/generate:
    post:
      summary: Transition(First-last frame) generation
      deprecated: false
      description: Transition(First-last frame) generation
      tags:
        - API Reference
      parameters:
        - name: API-KEY
          in: header
          description: api-key from PixVerse platform
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-Trace-Id
          in: header
          description: 'traceID format: UUID, must be unique for each request'
          required: true
          example: '{{$string.uuid}}'
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                prompt:
                  type: string
                  description: Prompt
                model:
                  type: string
                  description: Model version (now supports v3.5/v4/v4.5/v5)
                duration:
                  type: integer
                  description: >-
                    Video duration (5, 8 seconds, --model=v3.5 only allows 5,8;
                    --quality=1080p does not support 8s)
                quality:
                  type: string
                  description: Video quality ("360p"(Turbo), "540p", "720p", "1080p")
                motion_mode:
                  type: string
                  description: >-
                    Motion mode (normal, fast, --fast only available when
                    duration=5; --quality=1080p does not support fast) , not
                    supports on v5 
                seed:
                  type: integer
                  description: 'Random seed, range: 0 - 2147483647'
                first_frame_img:
                  type: integer
                  description: Image ID from Upload image API
                last_frame_img:
                  type: integer
                  description: Image ID from Upload image API
                sound_effect_switch:
                  type: string
                  description: >-
                    Set to true if you want to enable this feature. Default is
                    false.
                sound_effect_content:
                  type: string
                  description: >-
                    Sound effect content to generate. If not provided, a sound
                    effect will be automatically generated based on the video
                    content.
                lip_sync_switch:
                  type: string
                  description: >-
                    Set to true if you want to enable this feature. Default is
                    false.
                lip_sync_tts_content:
                  type: string
                  description: ~140 (UTF-8) characters
                lip_sync_tts_speaker_id:
                  type: string
                  description: 'id from Get speech tts list '
              required:
                - prompt
                - model
                - duration
                - quality
                - first_frame_img
                - last_frame_img
                - sound_effect_switch
                - sound_effect_content
                - lip_sync_switch
                - lip_sync_tts_content
                - lip_sync_tts_speaker_id
              x-apidog-orders:
                - prompt
                - model
                - duration
                - quality
                - motion_mode
                - seed
                - first_frame_img
                - last_frame_img
                - sound_effect_switch
                - sound_effect_content
                - lip_sync_switch
                - lip_sync_tts_content
                - lip_sync_tts_speaker_id
              x-apidog-ignore-properties: []
            example: |-
              {
                  "prompt": "transform into a puppy",
                  "model": "v5",
                  "duration": 5,
                  "quality": "540p",
                  //"motion_mode": "normal",
                  "first_frame_img": 0,
                  "last_frame_img": 0,
                  //"sound_effect_switch":true,
                  //"sound_effect_content":"",
                  //"lip_sync_tts_switch":true,
                  //"lip_sync_tts_content":"",
                  //"lip_sync_tts_speaker_id":"",
                  "seed": 0
              }
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/controller.ResponseData'
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-15123014-run
components:
  schemas:
    controller.ResponseData:
      type: object
      properties:
        ErrCode:
          type: integer
        ErrMsg:
          type: string
        Resp:
          $ref: '#/components/schemas/dto.V2OpenAPII2VResp'
      x-apidog-orders:
        - ErrCode
        - ErrMsg
        - Resp
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
    dto.V2OpenAPII2VResp:
      type: object
      properties:
        video_id:
          description: Video_id
          type: integer
      x-apidog-orders:
        - video_id
      x-apidog-ignore-properties: []
      x-apidog-folder: ''
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Upload Video&audio

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/media/upload:
    post:
      summary: Upload Video&audio
      deprecated: false
      description: >+
        1. Supported mime-type

        "video/mp4":       "mp4", "video/mov":       "mov", "video/webm":     
        "webm", "video/quicktime": "mov"

        "audio/mpeg":     "mp3", "audio/wav":      "wav", "audio/vnd.wave":
        "wav", "audio/x-wav":    "wav", "audio/x-m4a":    "m4a",
        "audio/aac":      "aac", "audio/x-aac":    "aac", "audio/wave":    
        "wav", "audio/mp4":      "mp3"


        2. Video File Limits

        - File size: Up to 50MB

        - Length: Up to 30 seconds

        - Resolution: Up to 1920px width or height


        3. Audio File Limits

        - File size: Up to 50MB

        - Length: Up to 30 seconds

      tags:
        - API Reference
      parameters:
        - name: Ai-Trace-Id
          in: header
          description: 'traceID format: UUID, must be unique for each request'
          required: true
          example: '{{$string.uuid}}'
          schema:
            type: string
        - name: API-KEY
          in: header
          description: api-key from PixVerse platform
          required: true
          example: your-api-key
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  format: binary
                  type: string
                  description: Either file or file_url is required.
                  example: ''
                file_url:
                  description: >-
                    media file from url, Either file or file_url is required.
                    supported mime-type : "video/mp4":       "mp4",
                    "video/mov":       "mov", "video/webm":      "webm",
                    "video/quicktime": "mov"


                    "audio/mpeg":     "mp3", "audio/wav":      "wav",
                    "audio/vnd.wave": "wav", "audio/x-wav":    "wav",
                    "audio/x-m4a":    "m4a", "audio/aac":      "aac",
                    "audio/x-aac":    "aac", "audio/wave":     "wav",
                    "audio/mp4":      "mp3"
                  example: >-
                    https://media.pixverse.ai/openapi%2F90f96bd5-5b77-461c-9b8e-c0e40526c9ca.mp4
                  type: string
            examples: {}
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      media_id:
                        type: integer
                        description: 'ID of the uploaded media  '
                      media_type:
                        type: string
                        description: 'Type of the uploaded media file '
                      url:
                        type: string
                        description: URL of the uploaded resource
                    required:
                      - media_id
                      - media_type
                      - url
                    x-apidog-orders:
                      - media_id
                      - media_type
                      - url
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
              example:
                ErrCode: 0
                ErrMsg: success
                Resp:
                  media_id: 0
                  media_type: audio
                  url: https://media.pixverse.ai/aaa.mp3
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-19094401-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```

# Speech(Lipsync) generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/lip_sync/generate:
    post:
      summary: Speech(Lipsync) generation
      deprecated: false
      description: |-
        Speech/Lipsync Generation
        4 casese for geneartion task
        1. source_video_id + audio_media_id
        2. source_video_id + lip_sync_tts_speaker_id + lip_sync_tts_conen
        3. video_media_id + audio_media_id
        4. video_media_id + lip_sync_tts_speaker_id + lip_sync_tts_conen
      tags:
        - API Reference
      parameters:
        - name: Ai-Trace-Id
          in: header
          description: 'traceID format: UUID, must be unique for each request'
          required: true
          example: '{{$string.uuid}}'
          schema:
            type: string
        - name: API-KEY
          in: header
          description: api-key from PixVerse platform
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                video_media_id:
                  type: integer
                  description: >-
                    'media_id' from the upload API with 'media_type = video' /
                    either source_video_id or video_media_id, not both.
                lip_sync_tts_speaker_id:
                  type: string
                  description: >-
                    id from Get speech tts list / either audio_media_id or
                    lip_sync_tts_speaker_id + lip_sync_tts_content, not both
                lip_sync_tts_content:
                  type: string
                  description: >-
                    lip sync content what you want / either audio_media_id or
                    lip_sync_tts_speaker_id + lip_sync_tts_content, not both
                source_video_id:
                  type: integer
                  description: >-
                    'video_id' returned from the generation API / either
                    source_video_id or video_media_id, not both.
                audio_media_id:
                  type: integer
                  description: >-
                    'media_id' from the upload API with 'media_type = audio' /
                    either audio_media_id or lip_sync_tts_speaker_id +
                    lip_sync_tts_content, not both
              x-apidog-orders:
                - video_media_id
                - source_video_id
                - audio_media_id
                - lip_sync_tts_speaker_id
                - lip_sync_tts_content
            example: |-
              {
                "video_media_id": 0,
                "source_video_id":0, //'video_id' returned from the generation API
                "audio_media_id":0, //'media_id' from the upload API with 'media_type = audio'
                "lip_sync_tts_speaker_id": "auto",
                "lip_sync_tts_content": "hello this is harry, where are you from?"
              }
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      video_id:
                        type: integer
                    required:
                      - video_id
                    x-apidog-orders:
                      - video_id
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
              example: |-
                {
                    "ErrCode": 0,
                    "ErrMsg": "Success",
                    "Resp": {
                        "video_id": 0
                }
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-19094278-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```

# Get Speech(Lipsync) tts list

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/lip_sync/tts_list:
    get:
      summary: Get Speech(Lipsync) tts list
      deprecated: false
      description: ''
      tags:
        - API Reference
      parameters:
        - name: page_num
          in: query
          description: ''
          required: true
          example: '1'
          schema:
            type: string
        - name: page_size
          in: query
          description: ''
          required: true
          example: '2'
          schema:
            type: string
        - name: Ai-Trace-Id
          in: header
          description: 'traceID format: UUID, must be unique for each request'
          required: true
          example: '{{$string.uuid}}'
          schema:
            type: string
        - name: API-KEY
          in: header
          description: api-key from PixVerse platform
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          text/plain:
            schema:
              type: string
            examples: {}
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      total:
                        type: integer
                      data:
                        type: array
                        items:
                          type: object
                          properties:
                            speaker_id:
                              type: string
                            name:
                              type: string
                          required:
                            - speaker_id
                            - name
                          x-apidog-orders:
                            - speaker_id
                            - name
                    required:
                      - total
                      - data
                    x-apidog-orders:
                      - total
                      - data
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
              example:
                ErrCode: 0
                ErrMsg: Success
                Resp:
                  total: 15
                  data:
                    - speaker_id: '7'
                      name: Harper
                    - speaker_id: '8'
                      name: Ava
                    - speaker_id: '3'
                      name: Isabella
                    - speaker_id: '9'
                      name: Sophia
                    - speaker_id: '1'
                      name: Emily
                    - speaker_id: '5'
                      name: Chloe
                    - speaker_id: '10'
                      name: Julia
                    - speaker_id: '11'
                      name: Mason
                    - speaker_id: '12'
                      name: Jack
                    - speaker_id: '4'
                      name: Liam
                    - speaker_id: '2'
                      name: James
                    - speaker_id: '13'
                      name: Oliver
                    - speaker_id: '6'
                      name: Adrian
                    - speaker_id: '14'
                      name: Ethan
                    - speaker_id: Auto
                      name: Auto
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-19094355-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Extend generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/extend/generate:
    post:
      summary: Extend generation
      deprecated: false
      description: Extend generation
      tags:
        - API Reference
      parameters:
        - name: Ai-Trace-Id
          in: header
          description: 'traceID format: UUID, must be unique for each request'
          required: true
          example: '{{$string.uuid}}'
          schema:
            type: string
        - name: API-KEY
          in: header
          description: api-key from PixVerse platform
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                source_video_id:
                  type: integer
                  description: >-
                    'video_id' returned from the generation API / either
                    source_video_id or video_media_id, not both.
                prompt:
                  type: string
                seed:
                  type: integer
                quality:
                  type: string
                duration:
                  type: integer
                model:
                  type: string
                  description: Model version (now supports v3.5/v4/v4.5 above)
                motion_mode:
                  type: string
                style:
                  type: string
                video_media_id:
                  type: integer
                  description: >-
                    'media_id' from the upload API with 'media_type = video' /
                    either source_video_id or video_media_id, not both.
              required:
                - prompt
                - seed
                - quality
                - duration
                - model
              x-apidog-orders:
                - source_video_id
                - video_media_id
                - prompt
                - seed
                - quality
                - duration
                - model
                - motion_mode
                - style
            example: |-
              {
                "source_video_id": 0,
                //"video_media_id":0, //'video_id' returned from the generation API
                "prompt": "across the universe",
                "seed": 123123,
                "quality": "540p",
                "duration": 5,
                "model": "v4.5",
                "motion_mode": "normal",
                //"style": "clay"
              }
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      video_id:
                        type: integer
                    required:
                      - video_id
                    x-apidog-orders:
                      - video_id
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
              example: |-
                {
                    "ErrCode": 0,
                    "ErrMsg": "Success",
                    "Resp": {
                        "video_id": 0
                }
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-19094393-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Sound effect generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/sound_effect/generate:
    post:
      summary: Sound effect generation
      deprecated: false
      description: ''
      tags:
        - API Reference
      parameters:
        - name: Ai-Trace-Id
          in: header
          description: ''
          required: true
          example: '123123'
          schema:
            type: string
        - name: API-KEY
          in: header
          description: ''
          required: true
          example: '123123'
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                source_video_id:
                  type: integer
                  description: video_id from generation
                original_sound_switch:
                  type: boolean
                  description: Keep original video sound
                sound_effect_content:
                  type: string
                  description: >-
                    Sound effect content to generate. If not provided, a sound
                    effect will be automatically generated based on the video
                    content.
                video_media_id:
                  type: integer
                  description: 'media_id from upload '
              x-apidog-orders:
                - source_video_id
                - video_media_id
                - original_sound_switch
                - sound_effect_content
            example:
              source_video_id: 123123
              original_sound_switch: true
              sound_effect_content: ''
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-19884196-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Fusion(reference to video) generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/fusion/generate:
    post:
      summary: Fusion(reference to video) generation
      deprecated: false
      description: ''
      tags:
        - API Reference
      parameters:
        - name: API-KEY
          in: header
          description: ''
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-trace-id
          in: header
          description: ''
          required: true
          example: your-Ai-trace-id
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                image_references:
                  type: array
                  items:
                    type: object
                    properties:
                      type:
                        type: string
                      img_id:
                        type: integer
                      ref_name:
                        type: string
                    required:
                      - type
                      - img_id
                      - ref_name
                prompt:
                  type: string
                model:
                  type: string
                duration:
                  type: integer
                quality:
                  type: string
                aspect_ratio:
                  type: string
                seed:
                  type: integer
              required:
                - image_references
                - prompt
                - model
                - duration
                - quality
                - aspect_ratio
                - seed
            example:
              image_references:
                - type: subject
                  img_id: 0
                  ref_name: dog
                - type: background
                  img_id: 0
                  ref_name: room
              prompt: '@dog plays at @room'
              model: v4.5
              duration: 5
              quality: 540p
              aspect_ratio: '16:9'
              seed: 123456789
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-19884194-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Restyle video generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/restyle/generate:
    post:
      summary: Restyle video generation
      deprecated: false
      description: ''
      tags:
        - API Reference
      parameters:
        - name: Ai-Trace-Id
          in: header
          description: ''
          required: true
          example: your-ai-trace-id
          schema:
            type: string
        - name: API-KEY
          in: header
          description: ''
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                source_video_id:
                  type: integer
                  description: >-
                    video_id from generation, one of source_video_id or
                    video_media_id should be provided
                restyle_id:
                  type: integer
                  description: >-
                    restyle_id from restyle_effect_list, one of restyle_id or
                    restyle_prompt should be provided
                seed:
                  type: integer
                video_media_id:
                  type: integer
                  description: >-
                    video_id from PixVerse API, one of source_video_id or
                    video_media_id should be provided
                restyle_prompt:
                  type: string
                  description: >-
                    prompt what you want to change, one of restyle_id or
                    restyle_prompt should be provided
              x-apidog-orders:
                - source_video_id
                - video_media_id
                - restyle_id
                - restyle_prompt
                - seed
            example:
              source_video_id: 0
              restyle_id: 0
              seed: 937433858
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      video_id:
                        type: integer
                      credits:
                        type: integer
                    required:
                      - video_id
                      - credits
                    x-apidog-orders:
                      - video_id
                      - credits
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
              example: |-
                {
                    "ErrCode": 0,
                    "ErrMsg": "Success",
                    "Resp": {
                        "video_id": 0,
                        "credits":0
                }
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-21992681-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Restyle effect list

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/restyle/list:
    get:
      summary: Restyle effect list
      deprecated: false
      description: ''
      tags:
        - API Reference
      parameters:
        - name: Ai-Trace-Id
          in: header
          description: ''
          required: true
          example: your-ai-trace-id
          schema:
            type: string
        - name: API-KEY
          in: header
          description: ''
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                page_num:
                  type: string
                page_size:
                  type: string
              required:
                - page_num
                - page_size
            example:
              page_num: string
              page_size: string
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-21992862-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Multi-transition video generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/multi_transition/generate:
    post:
      summary: Multi-transition video generation
      deprecated: false
      description: >-
        The Multi-transition(Multi-frame) feature allows you to generate a 1–30
        second video with consistent style and smooth transitions by providing
        2–7 keyframes.It is designed for professional creators, offering more
        fine-grained control over the video to ensure characters and actions
        remain coherent and controllable throughout the sequence.
      tags:
        - API Reference
      parameters:
        - name: API-KEY
          in: header
          description: ''
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-trace-id
          in: header
          description: ''
          required: true
          example: your-ai-trace-id
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                multi_transition:
                  type: array
                  items:
                    type: object
                    properties:
                      img_id:
                        type: integer
                      duration:
                        type: integer
                        description: ' not required for the last item'
                      prompt:
                        type: string
                    required:
                      - img_id
                      - duration
                    x-apidog-orders:
                      - img_id
                      - duration
                      - prompt
                  description: >-
                    1.multi_transition must be an array containing 2 to 7 items.

                    2.Each item in multi_transition should include: img_id
                    (required, integer), duration (required, integer, not
                    required for the last item), prompt (optional, string)
                model:
                  type: string
                  description: '"v3.5","v4","v4.5","v5"'
                quality:
                  type: string
                  description: '"360p","540p","720p","1080p"'
              required:
                - multi_transition
                - model
                - quality
              x-apidog-orders:
                - multi_transition
                - model
                - quality
            example:
              multi_transition:
                - img_id: 0
                  duration: 3
                  prompt: ''
                - img_id: 0
                  duration: 3
                  prompt: ''
                - img_id: 0
                  duration: 3
                  prompt: ''
                - img_id: 0
                  duration: 3
                  prompt: ''
                - img_id: 0
                  duration: 0
                  prompt: ''
              model: v5
              quality: 360p
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      video_id:
                        type: integer
                      credits:
                        type: integer
                    required:
                      - video_id
                      - credits
                    x-apidog-orders:
                      - video_id
                      - credits
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
              example: |-
                {
                    "ErrCode": 0,
                    "ErrMsg": "Success",
                    "Resp": {
                        "video_id": 0,
                        "credits":0
                }
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-24001841-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Swap mask generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/mask/selection:
    post:
      summary: Swap mask generation
      deprecated: false
      description: ''
      tags:
        - API Reference
      parameters:
        - name: API-KEY
          in: header
          description: ''
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-trace-id
          in: header
          description: ''
          required: true
          example: your-ai-trace-id
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                video_media_id:
                  type: integer
                  description: >-
                    media_id from uploaded video, one of source_video_id or
                    video_media_id should be provided. codec should be
                    h.264/h.265
                keyframe_id:
                  type: integer
                  description: >-
                    from 1 to The position of the last video frame. If not
                    provided, the default value is 1.
                source_video_id:
                  type: integer
                  description: >-
                    video_id from generation, one of source_video_id or
                    video_media_id should be provided
              x-apidog-orders:
                - source_video_id
                - video_media_id
                - keyframe_id
            example:
              video_media_id: 0
              keyframe_id: 0
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      keyframe_id:
                        type: integer
                      keyframe_url:
                        type: string
                      credits:
                        type: integer
                      mask_info:
                        type: array
                        items:
                          type: object
                          properties:
                            mask_id:
                              type: string
                            mask_name:
                              type: string
                            mask_url:
                              type: string
                          required:
                            - mask_id
                            - mask_name
                            - mask_url
                          x-apidog-orders:
                            - mask_id
                            - mask_name
                            - mask_url
                    required:
                      - keyframe_id
                      - keyframe_url
                      - credits
                      - mask_info
                    x-apidog-orders:
                      - keyframe_id
                      - keyframe_url
                      - credits
                      - mask_info
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-24001877-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Swap video generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/swap/generate:
    post:
      summary: Swap video generation
      deprecated: false
      description: >-
        source_video_id (or video_media_id), keyframe_id, and mask_id must all
        refer to the same video when performing mask generation.
      tags:
        - API Reference
      parameters:
        - name: API-KEY
          in: header
          description: ''
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-trace-id
          in: header
          description: ''
          required: true
          example: your-ai-trace-id
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                video_media_id:
                  type: integer
                  description: >-
                    media_id from uploaded video, one of source_video_id or
                    video_media_id should be provided
                keyframe_id:
                  type: integer
                  description: >-
                    from 1 to The position of the last video frame. If not
                    provided, the default value is 1.
                mask_id:
                  type: string
                  description: mask_id from mask generation
                img_id:
                  type: integer
                  description: img_id from upload image endpoint
                quality:
                  type: string
                  description: '"360p","540p","720p"'
                source_video_id:
                  type: integer
                  description: >-
                    video_id from generation, one of source_video_id or
                    video_media_id should be provided
              required:
                - keyframe_id
                - mask_id
                - img_id
                - quality
              x-apidog-orders:
                - source_video_id
                - video_media_id
                - keyframe_id
                - mask_id
                - img_id
                - quality
            example:
              video_media_id: 0
              keyframe_id: 1
              mask_id: '0'
              img_id: 0
              quality: 360p
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      video_id:
                        type: integer
                      credits:
                        type: integer
                    required:
                      - video_id
                      - credits
                    x-apidog-orders:
                      - video_id
                      - credits
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
              example: |-
                {
                    "ErrCode": 0,
                    "ErrMsg": "Success",
                    "Resp": {
                        "video_id": 0,
                        "credits":0
                }
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-24001839-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```
# Swap video generation

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /openapi/v2/video/swap/generate:
    post:
      summary: Swap video generation
      deprecated: false
      description: >-
        source_video_id (or video_media_id), keyframe_id, and mask_id must all
        refer to the same video when performing mask generation.
      tags:
        - API Reference
      parameters:
        - name: API-KEY
          in: header
          description: ''
          required: true
          example: your-api-key
          schema:
            type: string
        - name: Ai-trace-id
          in: header
          description: ''
          required: true
          example: your-ai-trace-id
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                video_media_id:
                  type: integer
                  description: >-
                    media_id from uploaded video, one of source_video_id or
                    video_media_id should be provided
                keyframe_id:
                  type: integer
                  description: >-
                    from 1 to The position of the last video frame. If not
                    provided, the default value is 1.
                mask_id:
                  type: string
                  description: mask_id from mask generation
                img_id:
                  type: integer
                  description: img_id from upload image endpoint
                quality:
                  type: string
                  description: '"360p","540p","720p"'
                source_video_id:
                  type: integer
                  description: >-
                    video_id from generation, one of source_video_id or
                    video_media_id should be provided
              required:
                - keyframe_id
                - mask_id
                - img_id
                - quality
              x-apidog-orders:
                - source_video_id
                - video_media_id
                - keyframe_id
                - mask_id
                - img_id
                - quality
            example:
              video_media_id: 0
              keyframe_id: 1
              mask_id: '0'
              img_id: 0
              quality: 360p
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  ErrCode:
                    type: integer
                  ErrMsg:
                    type: string
                  Resp:
                    type: object
                    properties:
                      video_id:
                        type: integer
                      credits:
                        type: integer
                    required:
                      - video_id
                      - credits
                    x-apidog-orders:
                      - video_id
                      - credits
                required:
                  - ErrCode
                  - ErrMsg
                  - Resp
                x-apidog-orders:
                  - ErrCode
                  - ErrMsg
                  - Resp
              example: |-
                {
                    "ErrCode": 0,
                    "ErrMsg": "Success",
                    "Resp": {
                        "video_id": 0,
                        "credits":0
                }
          headers: {}
          x-apidog-name: Success
      security: []
      x-apidog-folder: API Reference
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/772214/apis/api-24001839-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://app-api.pixverse.ai
    description: Prod Env
security: []

```