<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup>
// Configurações globais se necessário
</script>

<style>
/* Estilos globais já definidos no style.css */
</style>
