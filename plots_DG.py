import numpy as np, h5py, sys, time
import matplotlib; matplotlib.use('Agg')
#import matplotlib; matplotlib.use('pdf')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from   matplotlib import pylab
from   sklearn    import metrics


def valid_accuracy(y_true, y_prob):
    y_pred = np.argmax(y_prob, axis=1)
    return sum(y_pred==y_true)/len(y_true)


def get_LLH(sample, y_true):
    eff_class0, eff_class1 = [],[]
    for wp in ['p_LHTight', 'p_LHMedium', 'p_LHLoose']:
        y_class0 = sample[wp][y_true == 0]
        y_class1 = sample[wp][y_true != 0]
        eff_class0.append( sum(y_class0 == 0)/len(y_class0) )
        eff_class1.append( sum(y_class1 == 0)/len(y_class1) )
    return eff_class0, eff_class1


def plot_history(history, key='accuracy', file_name='outputs/history.png'):
    if len(history.epoch) < 2: return
    print('CLASSIFIER: saving training accuracy history in:', file_name)
    plt.figure(figsize=(12,8))
    pylab.grid(True)
    val = plt.plot(np.array(history.epoch)+1, 100*np.array(history.history[key]), label='Training')
    plt.plot(np.array(history.epoch)+1, 100*np.array(history.history['val_'+key]), '--',
             color=val[0].get_color(), label='Testing')
    min_acc = np.floor(100*min( history.history[key]+history.history['val_'+key] ))
    max_acc = np.ceil (100*max( history.history[key]+history.history['val_'+key] ))
    plt.xlim([1, max(history.epoch)+1])
    plt.xticks( np.append(1,np.arange(5,max(history.epoch)+2,step=5)) )
    plt.xlabel('Epochs',fontsize=25)
    plt.ylim( max(80,min_acc),max_acc )
    plt.yticks( np.arange(max(80,min_acc),max_acc+1,step=1) )
    plt.ylabel(key.title()+' (%)',fontsize=25)
    plt.legend(loc='lower right', fontsize=20, numpoints=3)
    plt.savefig(file_name)


def plot_distributions_DG(y_true, y_prob, tag=''):
    file_name = 'outputs/distributions'+tag+'.png'
    print('CLASSIFIER: saving test sample distributions in:', file_name)
    if max(y_true)+1 == 2:
        #label_dict = {0:'signal', 1:'background'}
        label_dict = {0:'iso electron', 1:'all others'}
    if max(y_true)+1 == 6:
        label_dict = {0:'iso electron', 1:'charge flip', 2:'photon conversion', 3:'b/c hadron decay',
                      4:'light flavor decay (bkg $\gamma$ + e$^\pm$)', 5:'light flavor decay (bkg hadron)'}
    plt.figure(figsize=(12,8))
    pylab.grid(True)
    pylab.xlim(0,100)
    pylab.ylim(1e-5,1e2)
    plt.xticks(np.arange(0,101,step=10))
    for n in np.arange(y_prob.shape[1]):
        class_probs   = 100*y_prob[:,0][y_true==n]
        class_weights = len(class_probs)*[100/len(y_true)]
        #class_weights = len(class_probs)*[100/len(class_probs)]
        bin_step = 0.5
        bins     = np.arange(0, 100+bin_step, bin_step)
        histtype ='step'
        pylab.hist( class_probs, bins=bins, label='Class '+str(n) + ': ' + label_dict[n],
                    histtype=histtype, weights=class_weights, log=True, lw=2 )
    plt.xlabel('Signal Probability (%)',fontsize=25)
    plt.ylabel('Distribution (% per '+ str(bin_step) +' % bin)', fontsize=25)
    plt.legend(loc='upper center', fontsize=17 if max(y_true)+1==2 else 15, numpoints=3)
    plt.savefig(file_name)


def separate_distributions(y_true, y_prob, sample, tag=''):
    from utils import make_labels
    file_name = 'outputs/distributions'+tag+'.png'
    labels = make_labels(sample, n_classes=6)
    print('CLASSIFIER: saving test sample distributions in:', file_name)
    label_dict = {0:'iso electron', 1:'charge flip', 2:'photon conversion', 3:'b/c hadron decay',
                  4:'light flavor decay (bkg $\gamma$ + e$^\pm$)', 5:'light flavor decay (bkg hadron)'}
    plt.figure(figsize=(12,8))
    pylab.grid(True)
    pylab.xlim(0,100)
    pylab.ylim(1e-5,1e2)
    plt.xticks(np.arange(0,101,step=10))
    for n in [0,1]:
        class_probs   = 100*y_prob[:,0][np.logical_and(y_true==0, labels==n)]
        class_weights = len(class_probs)*[100/len(y_true)]
        bin_step = 0.5
        bins     = np.arange(0, 100+bin_step, bin_step)
        histtype ='step'
        pylab.hist( class_probs, bins=bins, label='Class '+str(n) + ': ' + label_dict[n],
                    histtype=histtype, weights=class_weights, log=True, lw=2 )
    for n in [2,3,4,5]:
        class_probs   = 100*y_prob[:,0][np.logical_and(y_true==1, labels==n)]
        class_weights = len(class_probs)*[100/len(y_true)]
        bin_step = 0.5
        bins     = np.arange(0, 100+bin_step, bin_step)
        histtype ='step'
        pylab.hist( class_probs, bins=bins, label='Class '+str(n) + ': ' + label_dict[n],
                    histtype=histtype, weights=class_weights, log=True, lw=2 )
    plt.xlabel('Signal Probability (%)',fontsize=25)
    plt.ylabel('Distribution (% per '+ str(bin_step) +' % bin)', fontsize=25)
    plt.legend(loc='upper center', fontsize=15, numpoints=3)
    plt.savefig(file_name)


def plot_ROC_curves(sample, y_true, y_prob, ROC_type, tag=''):
    file_name = 'outputs/ROC'+str(ROC_type)+'_curve'+tag+'.png'
    print('CLASSIFIER: saving test sample ROC'+str(ROC_type)+' curve in:   ', file_name)
    eff_class0, eff_class1 = get_LLH(sample, y_true)
    fpr, tpr, threshold = metrics.roc_curve(y_true, y_prob[:,0], pos_label=0)
    signal_ratio        = sum(y_true==0)/len(y_true)
    accuracy            = tpr*signal_ratio + (1-fpr)*(1-signal_ratio)
    best_tpr, best_fpr  = tpr[np.argmax(accuracy)], fpr[np.argmax(accuracy)]
    colors = [ 'red', 'blue', 'green' ]
    labels = [ 'LLH tight', 'LLH medium', 'LLH loose' ]
    plt.figure(figsize=(12,8))
    pylab.grid(True)
    axes = plt.gca()
    axes.xaxis.set_ticks(np.arange(0, 101, 10))
    plt.xlabel('Signal Efficiency (%)',fontsize=25)
    if ROC_type == 1:
        plt.xlim([0, 100.25])
        plt.ylim([0, 100.5])
        axes.yaxis.set_ticks(np.arange(0, 101, 10))
        plt.ylabel('Background Rejection (%)',fontsize=25)
        plt.text(22, 34, 'AUC: '+str(format(metrics.auc(fpr,tpr),'.4f')),
                {'color': 'black', 'fontsize': 22}, va="center", ha="center")
        val = plt.plot(100*tpr, 100*(1-fpr), label='Signal vs Bkg', color='#1f77b4', lw=2)
        plt.scatter( 100*best_tpr, 100*(1-best_fpr), s=40, marker='o', c=val[0].get_color(),
                     label="{0:<16s} {1:>3.2f}%".format('Best Accuracy:',100*max(accuracy)) )
        for LLH in zip( eff_class0, eff_class1, colors, labels ):
            plt.scatter( 100*LLH[0], 100*(1-LLH[1]), s=40, marker='o', c=LLH[2], label='('+\
                         str( format(100*LLH[0],'.1f'))+'%, '+str( format(100*(1-LLH[1]),'.1f') )+\
                         ')'+r'$\rightarrow$'+LLH[3] )
        plt.legend(loc='lower left', fontsize=15, numpoints=3)
        plt.savefig(file_name)
    if ROC_type == 2:
        pylab.grid(False)
        len_0 = sum(fpr==0)
        x_min = min(60, 10*np.floor(10*eff_class0[0]))
        y_max = 100*np.ceil(max(1/fpr[np.argwhere(tpr >= x_min/100)[0]], 1/eff_class1[0])/100)
        plt.xlim([x_min, 100])
        plt.ylim([1,   y_max])
        LLH_scores = [1/fpr[np.argwhere(tpr >= value)[0]] for value in eff_class0]
        for n in np.arange(len(LLH_scores)):
            axes.axhline(LLH_scores[n], xmin=(eff_class0[n]-x_min/100)/(1-x_min/100), xmax=1,
            ls='--', linewidth=0.5, color='#1f77b4')
            axes.axvline(100*eff_class0[n], ymin=abs(1/eff_class1[n]-1)/(plt.yticks()[0][-1]-1),
            ymax=abs(LLH_scores[n]-1)/(plt.yticks()[0][-1]-1), ls='--', linewidth=0.5, color='tab:blue')
        for val in LLH_scores:
            plt.text(100.2, val, str(int(val)), {'color': '#1f77b4', 'fontsize': 10}, va="center", ha="left")
        axes.yaxis.set_ticks( np.append([1],plt.yticks()[0][1:]) )
        plt.ylabel('1/(Background Efficiency)',fontsize=25)
        val = plt.plot(100*tpr[len_0:], 1/fpr[len_0:], label='Signal vs Bkg', color='#1f77b4', lw=2)
        plt.scatter( 100*best_tpr, 1/best_fpr, s=40, marker='o', c=val[0].get_color(),
                     label="{0:<15s} {1:>3.2f}%".format('Best Accuracy:',100*max(accuracy)), zorder=10 )
        for LLH in zip( eff_class0, eff_class1, colors, labels ):
            plt.scatter( 100*LLH[0], 1/LLH[1], s=40, marker='o', c=LLH[2], label='('+\
                         str(format(100*LLH[0],'.1f'))+'%, '+str(format(1/LLH[1],'>3.0f'))+\
                         ')'+r'$\rightarrow$'+LLH[3] )
        plt.legend(loc='upper right', fontsize=15, numpoints=3)
        plt.savefig(file_name)
    if ROC_type == 3:
        best_threshold = threshold[np.argmax(accuracy)]
        plt.xlim([0, 100])
        plt.ylim([60, 100])
        plt.xlabel('Signal probability as threshold (%)', fontsize=25)
        plt.ylabel('(%)',fontsize=25)
        plt.plot( 100*threshold[1:], 100*tpr[1:], color='tab:blue', label='Signal efficiency', lw=2)
        plt.plot( 100*threshold[1:], 100*(1-fpr[1:]), color='tab:orange', label='Background rejection', lw=2)
        val = plt.plot(100*threshold[1:], 100*accuracy[1:], color='black', label='Accuracy', lw=2, zorder=10)
        std_accuracy  = 100*valid_accuracy(y_true, y_prob) #100*accuracy[np.argwhere(threshold<=0.5)[0][0]]
        plt.scatter( 50, std_accuracy, s=30, marker='D', c=val[0].get_color(),
                     label="{0:<10s} {1:>5.2f}%".format('Standard Accuracy:', std_accuracy), zorder=10 )

        plt.scatter( 100*best_threshold, 100*max(accuracy), s=40, marker='o', c=val[0].get_color(),
                     label="{0:<10s} {1:>5.2f}%".format('Best Accuracy:',100*max(accuracy)), zorder=10 )
        plt.legend(loc='lower center', fontsize=15, numpoints=3)
        plt.savefig(file_name)
    if ROC_type == 4:
        best_tpr = tpr[np.argmax(accuracy)]
        plt.xlim([60, 100.0])
        plt.ylim([80, 100.0])
        plt.xticks(np.arange(60,101,step=5))
        plt.yticks(np.arange(80,101,step=5))
        plt.xlabel('Signal efficiency (%)',fontsize=25)
        plt.ylabel('(%)',fontsize=25)
        plt.plot(100*tpr[1:], 100*(1-fpr[1:]), label='Background rejection', color='darkorange', lw=2)
        val = plt.plot(100*tpr[1:], 100*accuracy[1:], label='Accuracy', color='black', lw=2, zorder=10)
        plt.scatter( 100*best_tpr, 100*max(accuracy), s=40, marker='o', c=val[0].get_color(),
                     label="{0:<10s} {1:>5.2f}%".format('Best Accuracy:',100*max(accuracy)), zorder=10 )
        plt.legend(loc='lower center', fontsize=15, numpoints=3)
        plt.savefig(file_name)


def plot_image(cal_image, n_classes, e_class, images, image):
    #norm_type = None
    norm_type = colors.LogNorm(0.0001,1)
    limits = [-0.13499031, 0.1349903, -0.088, 0.088]
    e_image  = images.index(image)
    n_images = len(images)
    plot_number = n_classes*( e_image ) + e_class + 1
    plt.subplot(n_images, n_classes, plot_number)
    title='Class '+str(e_class)+' - Layer '+ image
    x_label, y_label = '' ,''
    x_ticks, y_ticks = [], []
    if e_image == n_images-1:
        x_label = '$\phi$'
        x_ticks = [limits[0],-0.05,0.05,limits[1]]
    if e_class == 0:
        y_label = '$\eta$'
        y_ticks = [limits[2],-0.05,0.0,0.05,limits[3]]
    plt.title(title,fontweight='bold')
    plt.xlabel(x_label,fontsize=14)
    plt.ylabel(y_label,fontsize=14)
    plt.xticks(x_ticks)
    plt.yticks(y_ticks)
    plt.imshow(cal_image.transpose(), cmap='Reds', extent=limits, norm=norm_type)
    plt.colorbar(pad=0.02)
    return


def cal_images(files, images, file_name='outputs/cal_images.png'):
    print('\nCLASSIFIER: saving calorimeter images in:', file_name,'\n')
    fig = plt.figure(figsize=(8,12))
    for e_class in np.arange( 0, len(files) ):
        input_file = h5py.File( files[e_class], 'r' )
        e_number   = np.random.randint( 0, len(input_file['data']), size=1 )[0]
        for image in images: plot_image( input_file['data/table_'+str(e_number)][image][0],
                                         len(files), e_class, images, image )
    hspace, wspace = 0.4, -0.6
    fig.subplots_adjust(left=-0.4, top=0.95, bottom=0.05, right=0.95, hspace=hspace, wspace=wspace)
    fig.savefig(file_name)
    plt.show() ; sys.exit()


def plot_scalars(sample, sample_trans, variable):
    bins = np.arange(-1,1,0.01)
    fig = plt.figure(figsize=(18,8))
    plt.subplot(1,2,1)
    pylab.xlim(-1,1)
    plt.title('Histogram')
    plt.xlabel('Value')
    plt.ylabel('Number of Entries')
    #pylab.hist(sample_trans[variable], bins=bins, histtype='step', density=True)
    pylab.hist(sample      [variable], bins=bins, histtype='step', density=False)
    plt.subplot(1,2,2)
    plt.title('Histogram')
    plt.xlabel('Value')
    plt.ylabel('Number of Entries')
    pylab.hist(sample_trans[variable], bins=bins)
    file_name = 'outputs/plots/scalars/'+variable+'.png'
    print('Printing:', file_name)
    plt.savefig(file_name)


def plot_tracks(tracks, labels, variable):
    tracks_var = {'efrac':{'idx':0, 'mean_lim':( 0,      3), 'max_lim':(0,    2), 'diff_lim':(0,    1)},
                  'deta' :{'idx':1, 'mean_lim':( 0, 0.0005), 'max_lim':(0, 0.03), 'diff_lim':(0, 0.04)},
                  'dphi' :{'idx':2, 'mean_lim':( 0,  0.001), 'max_lim':(0,  0.1), 'diff_lim':(0, 0.05)},
                  'd0'   :{'idx':3, 'mean_lim':( 0,    0.2), 'max_lim':(0,  0.1), 'diff_lim':(0,  0.3)},
                  'z0'   :{'idx':4, 'mean_lim':( 0,    0.5), 'max_lim':(0,  0.3), 'diff_lim':(0,   10)}}
    classes    = np.arange(max(labels)+1)
    n_e        = np.arange(len(labels)  )
    n_tracks   = np.sum(abs(tracks), axis=2)
    n_tracks   = np.array([len(np.where(n_tracks[n,:]!=0)[0]) for n in n_e])
    var        = tracks[..., tracks_var[variable]['idx']]
    var_mean   = np.array([np.mean(    var[n,:n_tracks[n]])  if n_tracks[n]!=0 else None for n in n_e])
    var_max    = np.array([np.max (abs(var[n,:n_tracks[n]])) if n_tracks[n]!=0 else None for n in n_e])
    var_diff   = np.array([np.mean(np.diff(np.sort(var[n,:n_tracks[n]])))
                           if n_tracks[n]>=2 else None for n in n_e])
    var_diff   = np.array([(np.max(var[n,:n_tracks[n]]) - np.min(var[n,:n_tracks[n]]))/(n_tracks[n]-1)
                           if n_tracks[n]>=2 else None for n in n_e])
    var_mean   = [var_mean[np.logical_and(labels==n, var_mean!=None)] for n in classes]
    var_max    = [var_max [np.logical_and(labels==n, var_max !=None)] for n in classes]
    var_diff   = [var_diff[np.logical_and(labels==n, var_diff!=None)] for n in classes]
    n_tracks   = [n_tracks[labels==n                                ] for n in classes]
    trk_mean   = [np.mean(n_tracks[n])                                for n in classes]
    fig  = plt.figure(figsize=(18,7))
    xlim = (0, 15)
    bins = np.arange(xlim[0], xlim[1]+2, 1)
    for n in [1,2]:
        plt.subplot(1,2,n); axes = plt.gca()
        plt.xlim(xlim)
        plt.xlabel('Number of tracks'      , fontsize=20)
        plt.xticks( np.arange(xlim[0],xlim[1]+1,1) )
        plt.ylabel('Normalized entries (%)', fontsize=20)
        title = 'Track number distribution (' + str(len(classes)) + '-class)'
        if n == 1: title += '\n(individually normalized)'
        weights = [len(n_tracks[n]) for n in classes] if n==1 else len(classes)*[len(labels)]
        weights = [len(n_tracks[n])*[100/weights[n]] for n in classes]
        plt.title(title, fontsize=20)
        label  =  ['class '+str(n)+' (mean: '+format(trk_mean[n],'3.1f')+')' for n in classes]
        plt.hist([n_tracks[n] for n in classes][::-1], bins=bins, lw=2, align='left',
                 weights=weights[::-1], label=label[::-1], histtype='step')
        plt.text(0.99, 0.05, '(sample: '+str(len(n_e))+' e)', {'color': 'black', 'fontsize': 12},
                 ha='right', va= 'center', transform=axes.transAxes)
        plt.legend(loc='upper right', fontsize=13)
    file_name = 'outputs/tracks_number.png'; print('Printing:', file_name)
    plt.savefig(file_name)
    fig     = plt.figure(figsize=(22,6)); n = 1
    metrics = {'mean':(var_mean, 'Average'), 'max':(var_max, 'Maximum absolute'),
               'diff':(var_diff, 'Average difference')}
    #metrics = {'mean':(var_mean, 'Average'), 'max':(var_mean, 'Average'),
    #           'diff':(var_mean, 'Average')}
    for metric in metrics:
        plt.subplot(1, 3, n); axes = plt.gca(); n+=1
        n_e    = sum([len(metrics[metric][0][n]) for n in classes])
        x1, x2 = tracks_var[variable][metric+'_lim']
        bins   = np.arange(0.9*x1, 1.1*x2, (x2-x1)/100)
        plt.xlim([x1, x2])
        plt.title (metrics[metric][1] + ' value of ' + str(variable) + '\'s', fontsize=20)
        plt.xlabel(metrics[metric][1] + ' value'                            , fontsize=20)
        plt.ylabel('Normalized entries (%)'                                 , fontsize=20)
        #weights = [len(metrics[metric][0][n])*[100/len(metrics[metric][0][n])] for n in classes]
        weights = [len(metrics[metric][0][n])*[100/n_e] for n in classes]
        plt.hist([metrics[metric][0][n] for n in classes][::-1], weights=weights[::-1], stacked=False,
                 histtype='step', label=['class '+str(n) for n in classes][::-1], bins=bins, lw=2)
        plt.text(0.01, 0.97, '(sample: '+str(n_e)+' e)', {'color': 'black', 'fontsize': 12},
                 ha='left', va= 'center', transform=axes.transAxes)
        plt.legend(loc='upper right', fontsize=13)
    file_name = 'outputs/tracks_'+str(variable)+'.png'; print('Printing:', file_name)
    plt.savefig(file_name)
