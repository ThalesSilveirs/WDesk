<template>
  <div class="custom-audio-player" :class="{ 'from-me': fromMe }">
    <button @click="togglePlay" class="play-btn">
      <PlayIcon v-if="!isPlaying" :size="18" class="icon" />
      <PauseIcon v-else :size="18" class="icon" />
    </button>

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
        <span v-if="isVoice" class="voice-badge">
          <MicIcon :size="11" />
          Áudio
        </span>
      </div>
    </div>

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
import { ref, computed } from 'vue'
import { Play as PlayIcon, Pause as PauseIcon, Mic as MicIcon } from 'lucide-vue-next'

const props = defineProps({
  src: { type: String, required: true },
  fromMe: { type: Boolean, default: false },
  isVoice: { type: Boolean, default: true }
})

const audioRef = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)

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
    audioRef.value.play()
    isPlaying.value = true
  }
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
</script>

<style scoped>
.custom-audio-player {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  min-width: 240px;
  max-width: 320px;
  width: 100%;
}

/* Specific theme for outbound message bubble style */
.custom-audio-player.from-me {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.play-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 0.2s, background-color 0.2s;
  box-shadow: 0 3px 8px rgba(16, 185, 129, 0.3);
}

.play-btn:hover {
  transform: scale(1.05);
  background: var(--accent-hover);
}

.player-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-container {
  position: relative;
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
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
  border-radius: 2px;
  pointer-events: none;
  position: absolute;
  left: 0;
  top: 0;
}

.custom-audio-player.from-me .progress-bar-fill {
  background: white;
}

.player-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time-display {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-family: monospace;
}

.custom-audio-player.from-me .time-display {
  color: rgba(255, 255, 255, 0.7);
}

.voice-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  color: var(--text-secondary);
  opacity: 0.8;
}

.custom-audio-player.from-me .voice-badge {
  color: rgba(255, 255, 255, 0.7);
}

.hidden-audio {
  display: none;
}

@media (max-width: 480px) {
  .custom-audio-player {
    min-width: 100%;
    padding: 8px 10px;
  }
}
</style>
