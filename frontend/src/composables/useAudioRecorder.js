import { ref, nextTick, onUnmounted } from 'vue'

export function useAudioRecorder() {
  const isRecording = ref(false)
  const hasRecording = ref(false)
  const recordedAudioUrl = ref(null)
  const recordedFile = ref(null)
  const recordingTime = ref(0)
  const recordingTimer = ref(null)
  const canvasRef = ref(null)

  let mediaRecorder = null
  let audioChunks = []
  let audioCtx = null
  let analyser = null
  let source = null
  let animationFrameId = null

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0')
    const secs = (seconds % 60).toString().padStart(2, '0')
    return `${mins}:${secs}`
  }

  const drawWaveform = () => {
    if (!canvasRef.value || !analyser) return
    const canvas = canvasRef.value
    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height

    analyser.fftSize = 32
    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const draw = () => {
      if (!isRecording.value) return
      animationFrameId = requestAnimationFrame(draw)
      analyser.getByteFrequencyData(dataArray)

      ctx.clearRect(0, 0, width, height)

      const barWidth = width / bufferLength
      let barHeight
      let x = 0

      for (let i = 0; i < bufferLength; i++) {
        barHeight = (dataArray[i] / 255) * height * 0.8
        if (barHeight < 2) barHeight = 2

        ctx.fillStyle = '#ef4444'
        const y = (height - barHeight) / 2

        ctx.fillRect(x, y, barWidth - 2, barHeight)
        x += barWidth
      }
    }

    draw()
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioChunks = []

      let options = { mimeType: 'audio/webm' }
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options = { mimeType: 'audio/ogg' }
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
          options = { mimeType: 'audio/mp4' }
          if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            options = {}
          }
        }
      }

      mediaRecorder = new MediaRecorder(stream, options)

      try {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)()
        analyser = audioCtx.createAnalyser()
        source = audioCtx.createMediaStreamSource(stream)
        source.connect(analyser)
      } catch (e) {
        console.warn("AudioContext não suportado ou falhou:", e)
      }

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop())

        if (animationFrameId) cancelAnimationFrame(animationFrameId)
        if (audioCtx) {
          audioCtx.close().catch(() => {})
          audioCtx = null
        }
        analyser = null

        if (audioChunks.length === 0) return

        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' })
        const extension = (mediaRecorder.mimeType || '').includes('ogg') ? 'ogg' :
                          (mediaRecorder.mimeType || '').includes('mp4') ? 'mp4' : 'webm'

        if (recordedAudioUrl.value) {
          URL.revokeObjectURL(recordedAudioUrl.value)
        }

        recordedAudioUrl.value = URL.createObjectURL(audioBlob)
        recordedFile.value = new File([audioBlob], `audio_record.${extension}`, { type: audioBlob.type })

        hasRecording.value = true
      }

      isRecording.value = true
      hasRecording.value = false
      recordedAudioUrl.value = null
      recordedFile.value = null
      recordingTime.value = 0

      mediaRecorder.start()

      recordingTimer.value = setInterval(() => {
        recordingTime.value++
      }, 1000)

      nextTick(() => {
        drawWaveform()
      })

    } catch (err) {
      console.error("Erro ao iniciar gravação de áudio:", err)
      alert("Não foi possível acessar o microfone. Verifique as permissões do seu navegador.")
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    isRecording.value = false
    clearInterval(recordingTimer.value)
  }

  const cancelRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.onstop = () => {
        const stream = mediaRecorder.stream
        if (stream) {
          stream.getTracks().forEach(track => track.stop())
        }
      }
      mediaRecorder.stop()
    }

    if (animationFrameId) cancelAnimationFrame(animationFrameId)
    if (audioCtx) {
      audioCtx.close().catch(() => {})
      audioCtx = null
    }
    analyser = null

    clearRecording()
  }

  const clearRecording = () => {
    if (recordedAudioUrl.value) {
      URL.revokeObjectURL(recordedAudioUrl.value)
    }
    isRecording.value = false
    hasRecording.value = false
    recordedAudioUrl.value = null
    recordedFile.value = null
    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
      recordingTimer.value = null
    }
    recordingTime.value = 0
    audioChunks = []
  }

  onUnmounted(() => {
    if (recordingTimer.value) clearInterval(recordingTimer.value)
    if (recordedAudioUrl.value) {
      URL.revokeObjectURL(recordedAudioUrl.value)
    }
  })

  return {
    isRecording,
    hasRecording,
    recordedAudioUrl,
    recordedFile,
    recordingTime,
    canvasRef,
    startRecording,
    stopRecording,
    cancelRecording,
    clearRecording,
    formatTime
  }
}
