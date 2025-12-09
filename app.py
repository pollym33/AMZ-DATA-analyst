import streamlit as st
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt

# --- 配置中文字体 (Streamlit Cloud默认支持部分中文字体，但为了保险我们尽量配置) ---
# 由于 Streamlit Cloud 环境下的字体路径不确定，我们先尝试使用默认配置，
# 如果图表显示方块，则需要联系Streamlit客服或查找如何上传字体文件。
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS'] # 尝试多种常见中文/Unicode字体
    plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题
except:
    pass # 忽略字体配置失败

# 页面配置
st.set_page_config(page_title="AMZ流量分析大师", layout="wide")

st.title("🛍️ Amazon 流量数据分析 & TikTok 策略生成器")
st.markdown("上传 CSV 流量文件 + 输入产品卖点，AI 自动生成深度分析报告。")

# 侧边栏：API Key配置
with st.sidebar:
    st.header("配置")
    api_key = st.text_input("1. 请输入 Gemini API Key:", type="password")
    
    # 确保配置了模型
    if api_key:
        genai.configure(api_key=api_key)
        
    st.markdown("---")
    st.markdown("API Key 从 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取")

# 输入区域
col1, col2 = st.columns(2)

with col1:
    product_context = st.text_area("2. 输入产品知识库 (卖点、Listing文案或URL内容):", height=200)

with col2:
    uploaded_file = st.file_uploader("3. 上传流量分析数据 (推荐UTF-8编码的CSV)", type=['csv'])

# 开始分析按钮
if st.button("开始深度分析 🚀"):
    if not api_key:
        st.error("❌ 请先在侧边栏输入 API Key")
    elif not uploaded_file or not product_context:
        st.error("❌ 请确保已上传文件并输入产品信息")
    else:
        try:
            # 1. 读取 CSV 文件：尝试多种编码
            uploaded_file.seek(0) # 确保文件指针在开头
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(uploaded_file, encoding='gbk')
                except UnicodeDecodeError:
                     uploaded_file.seek(0)
                     df = pd.read_csv(uploaded_file, encoding='latin1') # 最后的尝试

            # 清理列名和数据
            df.columns = [c.strip() for c in df.columns] 
            
            # --- 关键列名配置（请根据你的CSV文件进行修改！）---
            search_vol_col = '月搜索量' 
            keyword_col = '流量词'
            # --------------------------------------------------
            
            # 数据清洗：处理搜索量中的逗号和缺失值
            if search_vol_col in df.columns:
                # 去掉逗号，转换为数字 (errors='coerce' 会将非数字转为 NaN)
                df[search_vol_col] = df[search_vol_col].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce')
                df.dropna(subset=[search_vol_col], inplace=True)
            else:
                 st.error(f"❌ 数据处理失败：未找到关键列名 '{search_vol_col}'，请检查您的CSV表头。")
                 st.stop()
            
            # 2. 调用 Gemini 进行深度文本分析
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            
            # 构建 Prompt: 传递数据样本
            top_data_for_ai = df.nlargest(100, search_vol_col).to_csv(index=False) 
            
            prompt = f"""
            **【角色】**: 你是资深的亚马逊(Amazon)数据分析师及TikTok短视频营销专家。
            **【产品背景/知识库】**:
            {product_context}
            
            **【流量数据样本（已排序）】**:
            以下是基于月搜索量排序的TOP 100流量词数据样本，请注意分析其中的转化率和搜索趋势：
            {top_data_for_ai}
            
            **【任务】**:
            请严格按照以下结构输出深度分析报告（中文）：
            第一部分：数据概述统计
            第二部分：TOP5 流量入口深度解读（分析其市场意图和价值）
            第三部分：数据深度解读：市场特征与用户痛点分析
            第四部分：视频推广方向及脚本（包含3个方向和1个详细脚本）
            
            """
            
            with st.spinner('AI 正在清洗数据并生成深度报告中...'):
                response = model.generate_content(prompt)
                
            # 3. 展示结果
            
            # Part A: Python 绘制的真图表
            st.subheader("📊 TOP 5 流量入口可视化")
            
            top5 = df.nlargest(5, search_vol_col)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.barh(top5[keyword_col], top5[search_vol_col], color='teal')
            ax.set_xlabel(f'{search_vol_col} (月搜索量)')
            ax.set_title(f'Top 5 流量词搜索量分析')
            ax.invert_yaxis() 
            
            # 添加数值标签
            for bar in bars:
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2,
                        f'{width:,.0f}',
                        va='center')
            
            st.pyplot(fig)

            # Part B: AI 分析报告
            st.markdown("---")
            st.subheader("📝 AI 深度分析报告")
            st.markdown(response.text)

        except Exception as e:
            st.error(f"❌ 分析过程中出现致命错误。请检查CSV文件结构或联系支持。错误详情: {e}")
            
# 侧边栏提示
st.sidebar.markdown("---")
st.sidebar.markdown("📢 请确保您使用的 CSV 文件包含 **'流量词'** 和 **'月搜索量'** 两列。")
