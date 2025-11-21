<template>
  <a-spin :spinning="loading">
    <a-card title="用户资料设置" class="info-card" bordered>
      <template #extra>
        <a-space>
          <a-button size="small" @click="handleRefresh" :loading="loading">刷新</a-button>
          <a-button size="small" @click="handleReset" :disabled="!fieldList.length">恢复</a-button>
        </a-space>
      </template>

      <a-alert
        type="info"
        show-icon
        message="这些信息将直接体现在机器人问候语与业务回答里，请保持最新。"
        class="info-alert"
      />

      <div v-if="!fieldList.length && !loading" class="empty-wrap">
        <a-empty description="当前没有可配置的变量" />
      </div>

      <a-form
        v-else
        layout="vertical"
        :model="formState"
        class="info-form"
      >
        <a-row :gutter="[16, 8]">
          <a-col
            v-for="field in fieldList"
            :key="field"
            :xs="24"
            :md="12"
          >
            <a-form-item
              :label="getLabel(field)"
              :help="validationErrors[field]"
              :validate-status="validationErrors[field] ? 'error' : ''"
            >
              <a-input
                v-model:value="formState[field]"
                :placeholder="getPlaceholder(field)"
                :type="getInputType(field)"
                allow-clear
                @blur="() => validateField(field)"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <div class="form-actions">
          <a-button @click="handleReset" :disabled="!fieldList.length">恢复上次保存</a-button>
          <a-button type="primary" @click="handleSubmit" :loading="saving" :disabled="!fieldList.length">
            保存设置
          </a-button>
        </div>
      </a-form>
    </a-card>
  </a-spin>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue';
import { useGetInfoStore, useSetInfoStore } from '../apis/Info/infoStore';
import { mainStore } from '../store/index';
import { message } from 'ant-design-vue';

const getInfoStore = useGetInfoStore();
const setInfoStore = useSetInfoStore();
const userStore = mainStore();

const fieldList = ref([]);
const formState = reactive({});
const validationErrors = reactive({});
const originalValues = ref({});
const loading = ref(false);
const saving = ref(false);

const labels = {
  name: '客户姓名',
  amount: '账单金额'
};

const placeholders = {
  name: '例如：李先生 / 王女士',
  amount: '例如：8999'
};

const getLabel = (field) => labels[field] || field;
const getPlaceholder = (field) => placeholders[field] || `请输入${getLabel(field)}`;
const getInputType = (field) => field.toLowerCase().includes('amount') ? 'number' : 'text';

const snapshotForm = () => {
  const snapshot = {};
  fieldList.value.forEach((field) => {
    snapshot[field] = formState[field] ?? '';
  });
  return snapshot;
};

const clearState = () => {
  Object.keys(formState).forEach((key) => { delete formState[key]; });
  Object.keys(validationErrors).forEach((key) => { delete validationErrors[key]; });
};

const populateForm = (fields, values) => {
  clearState();
  fieldList.value = fields;
  fields.forEach((field) => {
    const value = values?.[field] ?? '';
    formState[field] = value ?? '';
    validationErrors[field] = '';
  });
  originalValues.value = snapshotForm();
};

const getInfo = async () => {
  loading.value = true;
  try {
    const formData = new FormData();
    formData.append('username', userStore.username);
    const res = await getInfoStore.getInfo(formData);
    const { fields = [], values = {} } = res.data || {};
    populateForm(fields, values);
  } catch (error) {
    console.error('Error fetching info:', error);
    message.error('获取信息失败，请稍后重试');
    populateForm([], {});
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => getInfo();

const handleReset = () => {
  if (!fieldList.value.length) return;
  fieldList.value.forEach((field) => {
    formState[field] = originalValues.value[field] ?? '';
    validationErrors[field] = '';
  });
  message.info('已恢复为最近一次加载的内容');
};

const validateField = (field) => {
  const value = (formState[field] ?? '').toString().trim();
  let error = '';

  if (field.toLowerCase() === 'name' && !value) {
    error = '请输入姓名';
  }

  if (field.toLowerCase().includes('amount')) {
    if (!value) {
      error = '请输入金额';
    } else if (Number.isNaN(Number(value))) {
      error = '金额需要填写数字';
    }
  }

  validationErrors[field] = error;
  return !error;
};

const validateForm = () => fieldList.value.every((field) => validateField(field));

const handleSubmit = async () => {
  if (!fieldList.value.length) return;
  if (!validateForm()) {
    message.warning('请先修正表单中的错误');
    return;
  }

  saving.value = true;
  const formData = new FormData();
  formData.append('username', userStore.username);
  fieldList.value.forEach((field) => {
    formData.append(field, formState[field] ?? '');
  });

  try {
    const res = await setInfoStore.setInfo(formData);
    if (res.status === 200) {
      message.success('信息已更新');
      originalValues.value = snapshotForm();
    } else {
      message.error('保存失败，请稍后再试');
    }
  } catch (error) {
    console.error('Error submitting form:', error);
    message.error('保存失败，请检查网络或稍后重试');
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  getInfo();
});
</script>

<style scoped>
.info-card {
  max-width: 960px;
  margin: 0 auto;
}

.info-alert {
  margin-bottom: 16px;
}

.info-form {
  margin-top: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.empty-wrap {
  padding: 48px 0;
}
</style>

