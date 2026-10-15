<template>
  <div style="display: inline-block">
    <el-button size="default" type="success" @click="handleImport()">
      <slot>导入</slot>
    </el-button>
    <el-dialog :title="dialogTitle" v-model="uploadShow" width="500px" append-to-body :close-on-click-modal="false">
      <div v-loading="loading">
        <!-- 阶段1：上传文件 -->
        <div v-if="stage === 'upload'">
          <el-upload
            ref="uploadRef"
            :limit="1"
            accept=".xlsx, .xls"
            :headers="props.upload.headers"
            :action="props.upload.url"
            :disabled="isUploading"
            :on-progress="handleFileUploadProgress"
            :on-success="handleFileSuccess"
            :auto-upload="false"
            drag
          >
            <i class="el-icon-upload"/>
            <div class="el-upload__text">
              将文件拖到此处，或
              <em>点击上传</em>
            </div>
            <template #tip>
            <div  class="el-upload__tip" style="color:red">提示：仅允许导入"xls"或"xlsx"格式文件！</div>
            </template>
          </el-upload>
          <div>
            <el-button type="warning" style="font-size:14px;margin-top: 20px" @click="importTemplate">下载导入模板</el-button>
            <el-button type="warning" style="font-size:14px;margin-top: 20px" @click="updateTemplate">批量更新模板</el-button>
          </div>
        </div>

        <!-- 阶段2：异步进度展示 -->
        <div v-else-if="stage === 'progress'" style="padding: 20px 0;">
          <div style="margin-bottom: 16px;">
            <el-progress :percentage="progressPercent" :status="progressStatus" :indeterminate="progressIndeterminate" />
          </div>
          <div style="color: #606266; font-size: 14px;">
            <div v-if="currentTask.description">{{ currentTask.description }}</div>
            <div v-else>正在处理中...</div>
          </div>
        </div>

        <!-- 阶段3：完成展示 -->
        <div v-else-if="stage === 'done'" style="padding: 20px 0; text-align: center;">
          <el-icon :size="48" :color="taskFailed ? '#f56c6c' : '#67c23a'">
            <CircleCheckFilled v-if="!taskFailed" />
            <CircleCloseFilled v-else />
          </el-icon>
          <div style="margin-top: 12px; font-size: 16px; font-weight: bold;">
            {{ taskFailed ? '导入失败' : '导入完成' }}
          </div>
          <div style="margin-top: 8px; color: #606266; font-size: 14px;" v-if="currentTask.description">
            {{ currentTask.description }}
          </div>
        </div>
      </div>
      <template #footer>
      <div  class="dialog-footer">
        <el-button v-if="stage === 'upload'" type="primary" :disabled="loading" @click="submitFileForm">确 定</el-button>
        <el-button v-if="stage === 'upload'" :disabled="loading" @click="uploadShow = false">取 消</el-button>
        <el-button v-if="stage !== 'upload'" type="primary" @click="closeAndRefresh" :disabled="stage === 'progress'">关 闭</el-button>
      </div>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup name="importExcel">
import { request, downloadFile } from '/@/utils/service';
import {inject, ref, computed} from "vue";
import { getBaseURL } from '/@/utils/baseUrl';
import { Session } from '/@/utils/storage';
import { ElMessageBox } from 'element-plus';
import { CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue';

const refreshView = inject<() => void>('refreshView')

let props = defineProps({
  upload: {
    type: Object,
    default () {
      return {
        // 是否显示弹出层
        open: true,
        // 弹出层标题
        title: '',
        // 是否禁用上传
        isUploading: false,
        // 是否更新已经存在的用户数据
        updateSupport: 0,
        // 设置上传的请求头部
        headers: { Authorization: 'JWT ' + Session.get('token') },
        // 上传的地址
        url: getBaseURL() + 'api/system/file/'
      }
    }
  },
  api: { // 导入接口地址
    type: String,
    default () {
      return undefined
    }
  },
  async: { // 是否使用异步导入（带进度展示）
    type: Boolean,
    default: false,
  }
})

let loading = ref(false)
const uploadRef = ref()
const uploadShow = ref(false)
const isUploading = ref(false)

// 异步导入相关状态
type Stage = 'upload' | 'progress' | 'done'
const stage = ref<Stage>('upload')
const taskFailed = ref(false)
const pollTimer = ref<number | null>(null)
const currentTask = ref<{ task_status: number; description: string }>({ task_status: 0, description: '' })

const progressPercent = computed(() => {
  const desc = currentTask.value.description || ''
  const match = desc.match(/已处理\s+(\d+)\/(\d+)/)
  if (match) {
    const current = parseInt(match[1])
    const total = parseInt(match[2])
    if (total > 0) return Math.min(Math.round((current / total) * 100), 99)
  }
  // 根据 task_status 判断
  if (currentTask.value.task_status === 2) return 100
  if (currentTask.value.task_status === 1) return 60
  return 0
})

const progressIndeterminate = computed(() => {
  const desc = currentTask.value.description || ''
  // "开始读取文件" / "解析 Excel 文件" 阶段显示不确定进度
  if (currentTask.value.task_status === 1 && !desc.match(/已处理\s+\d+\/\d+/)) {
    return true
  }
  return false
})

const progressStatus = computed(() => {
  if (currentTask.value.task_status === 3) return 'exception'
  if (currentTask.value.task_status === 2) return 'success'
  return undefined
})

const dialogTitle = computed(() => {
  if (stage.value === 'progress') return '导入中...'
  if (stage.value === 'done') return '导入结果'
  return props.upload.title || '导入数据'
})

/** 导入按钮操作 */
const handleImport = function () {
  stage.value = 'upload'
  taskFailed.value = false
  currentTask.value = { task_status: 0, description: '' }
  uploadShow.value = true
}

/** 下载模板操作 */
const importTemplate =function () {
  downloadFile({
    url: props.api + 'import_data/',
    params: {},
    method: 'get'
  })
}
/***
 * 批量更新模板
 */
const updateTemplate=function () {
  downloadFile({
    url: props.api + 'update_template/',
    params: {},
    method: 'get'
  })
}
// 文件上传中处理
const handleFileUploadProgress=function (event:any, file:any, fileList:any) {
  isUploading.value = true
}

// 关闭弹窗并刷新
const closeAndRefresh = function () {
  uploadShow.value = false
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
  if (!taskFailed.value) {
    refreshView?.()
  }
}

// 轮询异步导入任务状态
const startPolling = function (taskId: number) {
  const url = '/system/download_center/' + taskId + '/'
  pollTimer.value = window.setInterval(async () => {
    try {
      const res = await request({ url, method: 'get' })
      const data = res.data
      currentTask.value = {
        task_status: data.task_status,
        description: data.description || '',
      }

      // 2=完成, 3=失败
      if (data.task_status === 2 || data.task_status === 3) {
        clearInterval(pollTimer.value!)
        pollTimer.value = null
        taskFailed.value = data.task_status === 3
        stage.value = 'done'
      }
    } catch (e) {
      // 轮询失败不中断
    }
  }, 2000)
}

// 文件上传成功处理
const handleFileSuccess=function (response:any, file:any, fileList:any) {
  isUploading.value = false
  loading.value = true
  uploadRef.value.clearFiles()

  const postData: Record<string, any> = { url: response.data.url }
  if (props.async) {
    postData.async = true
  }

  return request({
    url: props.api + 'import_data/',
    method: 'post',
    timeout: 600000,
    data: postData
  }).then((response:any) => {
    loading.value = false

    if (props.async && response.data?.task_id) {
      // 异步导入：进入进度展示阶段
      stage.value = 'progress'
      currentTask.value.description = response.msg || '任务已创建，等待执行...'
      startPolling(response.data.task_id)
    } else {
      // 同步导入（原有逻辑）
      ElMessageBox.alert('导入成功', '导入完成', {
        confirmButtonText: 'OK',
        callback: () => {
          uploadShow.value = false
          refreshView?.()
        },
      })
    }
  }).catch(() => {
    loading.value = false
  })
}

// 提交上传文件
const submitFileForm=function () {
  uploadRef.value.submit()
}
</script>

<style scoped>

</style>
