-- 为读书内容表添加签到列表字段
ALTER TABLE read_content ADD COLUMN sign_list VARCHAR(5000) COMMENT '签到列表';
