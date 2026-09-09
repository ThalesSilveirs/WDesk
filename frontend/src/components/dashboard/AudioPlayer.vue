<template>
  <div class="custom-audio-player" :class="{ 'from-me': fromMe }">
    <!-- Play/Pause Primary Button -->
    <button @click="togglePlay" class="play-btn" :title="isPlaying ? 'Pausar (Espaço)' : 'Reproduzir (Espaço)'">
      <PlayIcon v-if="!isPlaying" :size="18" class="icon" />
      <PauseIcon v-else :size="18" class="icon" />
    </button>

    <!-- Player Body: Progress Track & Time Meta -->
    <div class="player-body">
      <!-- Progress Bar Track -->
      <div class="progress-container">
        <input 
          type="range" 
          min="0" 
          :max="duration || 100" 
          :value="currentTime" 
          @input="seek"
          class="seek-bar"
        />
        <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>

      <div class="player-meta">
        <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
        
        <div class="meta-right">
          <!-- Skip 5s backward -->
          <button @click="skip(-5)" class="skip-btn" title="Voltar 5 segundos">
            <RotateCcwIcon :size="12" />
            <span>-5s</span>
          </button>

          <!-- Skip 5s forward -->
          <button @click="skip(5)" class="skip-btn" title="Avançar 5 segundos">
            <RotateCwIcon :size="12" />
            <span>+5s</span>
          </button>

          <!-- Voice note badge -->
          <span v-if="isVoice" class="voice-badge">
            <MicIcon :size="11" />
            Áudio
          </span>
        </div>
      </div>
    </div>

    <!-- Playback Rate Pill Button (1x -> 1.25x -> 1.5x -> 2x) -->
    <button 
      @click="cyclePlaybackRate" 
      class="speed-btn" 
      :class="{ 'speed-active': playbackRate !== 1 }"
      :title="'Velocidade: ' + playbackRate + 'x (Clique para alternar)'"
    >
      {{ playbackRate }}x
    </button>

    <!-- Hidden native audio element -->
    <audio 
      ref="audioRef" 
      :src="src" 
      @timeupdate="onTimeUpdate" 
      @loadedmetadata="onLoadedMetadata" 
      @ended="onEnded"
      class="hidden-audio"
    ></audio>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import {
  Play as PlayIcon,
  Pause as PauseIcon,
  Mic as MicIcon,
  RotateCcw as RotateCcwIcon,
  RotateCw as RotateCwIcon
} from 'lucide-vue-next'

const props = defineProps({
  src: { type: String, required: true },
  fromMe: { type: Boolean, default: false },
  isVoice: { type: Boolean, default: true }
})

const audioRef = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const playbackRate = ref(1)

const speeds = [1, 1.25, 1.5, 2]

const progressPercent = computed(() => {
  if (!duration.value) return 0
  return (currentTime.value / duration.value) * 100
})

const togglePlay = () => {
  if (!audioRef.value) return
  if (isPlaying.value) {
    audioRef.value.pause()
    isPlaying.value = false
  } else {
    audioRef.value.playbackRate = playbackRate.value
    audioRef.value.play()
    isPlaying.value = true
  }
}

const cyclePlaybackRate = () => {
  const currentIndex = speeds.indexOf(playbackRate.value)
  const nextIndex = (currentIndex + 1) % speeds.length
  playbackRate.value = speeds[nextIndex]

  if (audioRef.value) {
    audioRef.value.playbackRate = playbackRate.value
  }
}

const skip = (deltaSeconds) => {
  if (!audioRef.value) return
  const newTime = Math.max(0, Math.min(duration.value || 0, audioRef.value.currentTime + deltaSeconds))
  audioRef.value.currentTime = newTime
  currentTime.value = newTime
}

const seek = (e) => {
  if (!audioRef.value) return
  const val = parseFloat(e.target.value)
  audioRef.value.currentTime = val
  currentTime.value = val
}

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
  }
}

const onLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
    audioRef.value.playbackRate = playbackRate.value
  }
}

const onEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
}

const formatTime = (secs) => {
  if (isNaN(secs) || secs === Infinity) return '0:00'
  const minutes = Math.floor(secs / 60)
  const seconds = Math.floor(secs % 60)
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`
}

// Ensure audio pauses if unmounted
onUnmounted(() => {
  if (audioRef.value) {
    audioRef.value.pause()
    audioRef.value.src = ''
  }
})
</script>

<style scoped>
.custom-audio-player {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 2px;
  border-radius: 12px;
  background: transparent;
  min-width: 260px;
  max-width: 350px;
  width: 100%;
}

/* Outbound audio player adjustments */
.custom-audio-player.from-me {
  background: transparent;
}

.play-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
  box-shadow: 0 3px 8px rgba(16, 185, 129, 0.3);
}

.play-btn:hover {
  transform: scale(1.06);
  background: var(--accent-hover);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.play-btn:active {
  transform: scale(0.96);
}

.player-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.progress-container {
  position: relative;
  width: 100%;
  height: 5px;
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
}

.custom-audio-player.from-me .progress-container {
  background: rgba(0, 0, 0, 0.14);
}

.seek-bar {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
  z-index: 2;
}

.progress-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  pointer-events: none;
  position: absolute;
  left: 0;
  top: 0;
}

.player-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
}

.time-display {
  font-size: 0.72rem;
  color: var(--msg-meta-received, var(--text-secondary));
  font-family: monospace;
  white-space: nowrap;
}

.custom-audio-player.from-me .time-display {
  color: var(--msg-meta-sent, var(--text-secondary));
}

.meta-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.skip-btn {
  background: transparent;
  border: none;
  color: var(--msg-meta-received, var(--text-secondary));
  font-size: 0.65rem;
  display: flex;
  align-items: center;
  gap: 2px;
  cursor: pointer;
  padding: 1px 4px;
  border-radius: 4px;
  opacity: 0.8;
  transition: all 0.15s ease;
}

.skip-btn:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.08);
}

.custom-audio-player.from-me .skip-btn {
  color: var(--msg-meta-sent, var(--text-secondary));
}

.custom-audio-player.from-me .skip-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

.voice-badge {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.68rem;
  color: var(--msg-meta-received, var(--text-secondary));
  opacity: 0.85;
}

.custom-audio-player.from-me .voice-badge {
  color: var(--msg-meta-sent, var(--text-secondary));
}

/* Speed Pill Button */
.speed-btn {
  background: rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border);
  color: var(--msg-meta-received, var(--text-secondary));
  font-size: 0.75rem;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 8px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
  min-width: 38px;
  text-align: center;
}

.speed-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  color: var(--text-primary);
}

.speed-btn.speed-active {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
}

.custom-audio-player.from-me .speed-btn {
  background: rgba(0, 0, 0, 0.06);
  border-color: var(--border);
  color: var(--msg-meta-sent, var(--text-secondary));
}

.custom-audio-player.from-me .speed-btn.speed-active {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
}

.hidden-audio {
  display: none;
}

@media (max-width: 480px) {
  .custom-audio-player {
    min-width: 100%;
    padding: 8px 10px;
    gap: 8px;
  }

  .skip-btn span {
    display: none;
  }
}
</style>
