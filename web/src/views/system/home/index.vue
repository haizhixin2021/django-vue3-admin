<template>
	<div class="home-container">
		<div style="height: 100%; display: flex; justify-content: center; flex-direction: column;">
			<div style="text-align: center;">
				<img draggable="false" src="./home.png" style="margin: auto;">
			</div>
		</div>
	</div>
</template>

<script lang="ts" name="home">
import { defineComponent } from 'vue';

export default defineComponent({
	name: 'home',
	setup() {
		return {};
	}
});
</script>

<style scoped lang="scss">
.home-container {
	margin-top: 100px;
	overflow: hidden;
}
</style>
