function plt_csv(filename)
    % PLT_CSV 读取 CSV 文件并绘制折线图
    % 使用方式: plt_csv('sensor_data.csv')

    % 读取 CSV 文件
    data = readmatrix(filename);

    % 确保 CSV 文件至少包含两列
    if size(data, 2) < 2
        error('CSV 文件应包含至少两列数据（时间 和 数值）。');
    end

    % 提取时间和数值
    time = data(:,1);    % 第一列: 时间
    values = data(:,4);  % 第二列: 数值（注意，这里改回第二列）

    % 创建折线图
    figure;
    plot(time, values, 'Color', [0, 0.4470, 0.7410], 'LineWidth', 1.5);  
    % 颜色改为 MATLAB 默认蓝色 [0, 0.4470, 0.7410]
    % 线宽 1.5

    % 设置坐标轴标签和标题
    xlabel('Hour', 'FontSize', 12);
    ylabel('Mole%', 'FontSize', 12);
    title('Component G in Product', 'FontSize', 14);

   % 启用网格，提高可读性
    grid on;
    
    % 设置 X 轴范围
    xlim([min(time), max(time)]);

    % 设置 Y 轴范围
    ylim([min(values) - 0.5, max(values) + 0.5]);

    % 显示折线图
    disp('CSV 数据绘制完成！');
end
